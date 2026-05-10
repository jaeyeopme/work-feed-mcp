"""JSONL-to-SQLite ingest implementation."""

from __future__ import annotations

import json
import sqlite3
import sys
import uuid
from dataclasses import dataclass
from datetime import UTC, datetime
from pathlib import Path
from typing import TextIO

from upwork_ingest.errors import UsageError, ValidationError
from upwork_ingest.models import CollectorRecord, validate_payload
from upwork_ingest.schema import initialize_schema


@dataclass(frozen=True, slots=True)
class IngestResult:
    run_id: str
    record_count: int
    db_path: str
    input_path: str | None
    source_query: str | None


def utc_now() -> str:
    return datetime.now(UTC).replace(microsecond=0).isoformat().replace("+00:00", "Z")


def read_jsonl(stream: TextIO) -> list[CollectorRecord]:
    records: list[CollectorRecord] = []
    for line_number, line in enumerate(stream, start=1):
        stripped = line.strip()
        if not stripped:
            continue
        try:
            decoded = json.loads(stripped)
        except json.JSONDecodeError as exc:
            raise ValidationError(f"malformed JSONL at line {line_number}") from exc
        try:
            records.append(validate_payload(decoded))
        except ValidationError as exc:
            raise ValidationError(f"invalid collector record at line {line_number}: {exc}") from exc
    return records


def _open_input(input_path: str) -> tuple[TextIO, bool]:
    if input_path == "-":
        return sys.stdin, False
    try:
        return Path(input_path).open("r", encoding="utf-8"), True
    except OSError as exc:
        raise UsageError("input path is missing or unreadable") from exc


def load_records(input_path: str) -> list[CollectorRecord]:
    stream, should_close = _open_input(input_path)
    try:
        return read_jsonl(stream)
    finally:
        if should_close:
            stream.close()


def _insert_run(
    connection: sqlite3.Connection,
    *,
    run_id: str,
    source_query: str | None,
    input_path: str | None,
    started_at: str,
) -> None:
    connection.execute(
        """
        INSERT INTO ingest_runs (
          run_id, source_query, input_path, started_at, completed_at, record_count, status
        ) VALUES (?, ?, ?, ?, NULL, 0, 'running')
        """,
        (run_id, source_query, input_path, started_at),
    )


def _complete_run(
    connection: sqlite3.Connection, *, run_id: str, completed_at: str, record_count: int
) -> None:
    connection.execute(
        """
        UPDATE ingest_runs
        SET completed_at = ?, record_count = ?, status = 'completed'
        WHERE run_id = ?
        """,
        (completed_at, record_count, run_id),
    )


def _fail_run(connection: sqlite3.Connection, *, run_id: str, completed_at: str) -> None:
    connection.execute(
        """
        UPDATE ingest_runs
        SET completed_at = ?, status = 'failed'
        WHERE run_id = ?
        """,
        (completed_at, run_id),
    )


def _upsert_job(connection: sqlite3.Connection, record: CollectorRecord, observed_at: str) -> None:
    connection.execute(
        """
        INSERT INTO jobs (
          job_id, source, title, description, url, posted_at, job_type, contractor_tier,
          hourly_min, hourly_max, fixed_amount, raw_id, content_hash, first_seen_at, last_seen_at
        ) VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
        ON CONFLICT(job_id) DO UPDATE SET
          source = excluded.source,
          title = excluded.title,
          description = excluded.description,
          url = excluded.url,
          posted_at = excluded.posted_at,
          job_type = excluded.job_type,
          contractor_tier = excluded.contractor_tier,
          hourly_min = excluded.hourly_min,
          hourly_max = excluded.hourly_max,
          fixed_amount = excluded.fixed_amount,
          raw_id = excluded.raw_id,
          content_hash = excluded.content_hash,
          last_seen_at = excluded.last_seen_at
        """,
        (
            record.job_id,
            record.source,
            record.title,
            record.description,
            record.url,
            record.posted_at,
            record.job_type,
            record.contractor_tier,
            record.hourly_min,
            record.hourly_max,
            record.fixed_amount,
            record.raw_id,
            record.content_hash,
            observed_at,
            observed_at,
        ),
    )


def _replace_skills(connection: sqlite3.Connection, record: CollectorRecord) -> None:
    connection.execute("DELETE FROM job_skills WHERE job_id = ?", (record.job_id,))
    connection.executemany(
        "INSERT OR IGNORE INTO job_skills (job_id, skill) VALUES (?, ?)",
        [(record.job_id, skill) for skill in record.skills],
    )


def _insert_observation(
    connection: sqlite3.Connection,
    *,
    record: CollectorRecord,
    run_id: str,
    source_query: str | None,
    observed_at: str,
    line_number: int,
) -> None:
    observation_id = f"{run_id}:{line_number}:{record.content_hash[:16]}"
    connection.execute(
        """
        INSERT OR IGNORE INTO job_observations (
          observation_id, job_id, run_id, source_query, observed_at, content_hash
        ) VALUES (?, ?, ?, ?, ?, ?)
        """,
        (observation_id, record.job_id, run_id, source_query, observed_at, record.content_hash),
    )


def _insert_raw_record(
    connection: sqlite3.Connection,
    *,
    record: CollectorRecord,
    run_id: str,
    received_at: str,
    line_number: int,
) -> None:
    raw_record_id = f"{run_id}:{line_number}:raw:{record.content_hash[:16]}"
    connection.execute(
        """
        INSERT OR IGNORE INTO raw_records (
          raw_record_id, job_id, run_id, content_hash, received_at, payload_json
        ) VALUES (?, ?, ?, ?, ?, ?)
        """,
        (
            raw_record_id,
            record.job_id,
            run_id,
            record.content_hash,
            received_at,
            record.payload_json,
        ),
    )


def ingest_records(
    records: list[CollectorRecord],
    *,
    db_path: str,
    input_path: str | None,
    source_query: str | None,
    run_id: str | None = None,
) -> IngestResult:
    resolved_run_id = run_id or f"run-{uuid.uuid4()}"
    started_at = utc_now()
    path = Path(db_path)
    if path.parent != Path(""):
        path.parent.mkdir(parents=True, exist_ok=True)
    connection = sqlite3.connect(path)
    try:
        initialize_schema(connection)
        _insert_run(
            connection,
            run_id=resolved_run_id,
            source_query=source_query,
            input_path=input_path,
            started_at=started_at,
        )
        for line_number, record in enumerate(records, start=1):
            observed_at = utc_now()
            _upsert_job(connection, record, observed_at)
            _replace_skills(connection, record)
            _insert_observation(
                connection,
                record=record,
                run_id=resolved_run_id,
                source_query=source_query,
                observed_at=observed_at,
                line_number=line_number,
            )
            _insert_raw_record(
                connection,
                record=record,
                run_id=resolved_run_id,
                received_at=observed_at,
                line_number=line_number,
            )
        _complete_run(
            connection, run_id=resolved_run_id, completed_at=utc_now(), record_count=len(records)
        )
        connection.commit()
    except Exception:
        connection.rollback()
        try:
            initialize_schema(connection)
            _fail_run(connection, run_id=resolved_run_id, completed_at=utc_now())
            connection.commit()
        except Exception:
            connection.rollback()
        raise
    finally:
        connection.close()
    return IngestResult(
        run_id=resolved_run_id,
        record_count=len(records),
        db_path=str(path),
        input_path=input_path,
        source_query=source_query,
    )


def ingest_jsonl(
    *, db_path: str, input_path: str, source_query: str | None, run_id: str | None = None
) -> IngestResult:
    records = load_records(input_path)
    return ingest_records(
        records,
        db_path=db_path,
        input_path=None if input_path == "-" else input_path,
        source_query=source_query,
        run_id=run_id,
    )
