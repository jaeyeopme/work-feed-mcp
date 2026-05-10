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

from upwork_app.core.errors import UsageError, ValidationError
from upwork_app.db.schema import initialize_schema
from upwork_app.domain.collector_record import CollectorRecord, validate_payload
from upwork_app.repositories import ingestion as ingestion_repository


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
        ingestion_repository.insert_run(
            connection,
            run_id=resolved_run_id,
            source_query=source_query,
            input_path=input_path,
            started_at=started_at,
        )
        for line_number, record in enumerate(records, start=1):
            observed_at = utc_now()
            ingestion_repository.upsert_job(connection, record, observed_at)
            ingestion_repository.replace_skills(connection, record)
            ingestion_repository.insert_observation(
                connection,
                record=record,
                run_id=resolved_run_id,
                source_query=source_query,
                observed_at=observed_at,
                line_number=line_number,
            )
            ingestion_repository.insert_raw_record(
                connection,
                record=record,
                run_id=resolved_run_id,
                received_at=observed_at,
                line_number=line_number,
            )
        ingestion_repository.complete_run(
            connection, run_id=resolved_run_id, completed_at=utc_now(), record_count=len(records)
        )
        connection.commit()
    except Exception:
        connection.rollback()
        try:
            initialize_schema(connection)
            ingestion_repository.fail_run(
                connection, run_id=resolved_run_id, completed_at=utc_now()
            )
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
