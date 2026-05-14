"""JSONL-to-SQLite ingest implementation."""

from __future__ import annotations

import json
import sqlite3
import sys
from dataclasses import dataclass
from datetime import UTC, datetime
from pathlib import Path
from typing import Any, TextIO

from upwork_app.core.errors import UsageError, ValidationError
from upwork_app.db.schema import initialize_schema
from upwork_app.domain.collector_record import CollectorRecord, validate_payload
from upwork_app.repositories import ingestion as ingestion_repository


@dataclass(frozen=True, slots=True)
class IngestResult:
    seen_count: int
    inserted_count: int
    skipped_count: int
    new_jobs: tuple[dict[str, Any], ...]
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


def _job_response(record: CollectorRecord) -> dict[str, Any]:
    return {
        "job_id": record.job_id,
        "source": record.source,
        "title": record.title,
        "description": record.description,
        "url": record.url,
        "skills": list(record.skills),
        "posted_at": record.posted_at,
        "job_type": record.job_type,
        "contractor_tier": record.contractor_tier,
        "hourly_min": record.hourly_min,
        "hourly_max": record.hourly_max,
        "fixed_amount": record.fixed_amount,
        "raw_id": record.raw_id,
    }


def ingest_records_into_connection(
    connection: sqlite3.Connection,
    records: list[CollectorRecord],
    *,
    db_path: str,
    input_path: str | None,
    source_query: str | None,
) -> IngestResult:
    """Insert collector records using an existing transaction owner."""

    new_jobs: list[dict[str, Any]] = []
    for record in records:
        if ingestion_repository.insert_job_if_new(connection, record, utc_now()):
            ingestion_repository.insert_skills(connection, record)
            new_jobs.append(_job_response(record))
    return IngestResult(
        seen_count=len(records),
        inserted_count=len(new_jobs),
        skipped_count=len(records) - len(new_jobs),
        new_jobs=tuple(new_jobs),
        db_path=db_path,
        input_path=input_path,
        source_query=source_query,
    )


def ingest_records(
    records: list[CollectorRecord],
    *,
    db_path: str,
    input_path: str | None,
    source_query: str | None,
) -> IngestResult:
    path = Path(db_path)
    if path.parent != Path(""):
        path.parent.mkdir(parents=True, exist_ok=True)
    connection = sqlite3.connect(path)
    try:
        initialize_schema(connection)
        result = ingest_records_into_connection(
            connection,
            records,
            db_path=str(path),
            input_path=input_path,
            source_query=source_query,
        )
        connection.commit()
        return result
    except Exception:
        connection.rollback()
        raise
    finally:
        connection.close()


def ingest_jsonl(*, db_path: str, input_path: str, source_query: str | None) -> IngestResult:
    records = load_records(input_path)
    return ingest_records(
        records,
        db_path=db_path,
        input_path=None if input_path == "-" else input_path,
        source_query=source_query,
    )
