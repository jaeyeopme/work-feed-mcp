"""Persistence for collector-emitted normalized JSON records only."""

from __future__ import annotations

import hashlib
import json
import sqlite3
import uuid
from collections.abc import Mapping
from dataclasses import dataclass
from datetime import UTC, datetime
from typing import Any, Final

COLLECTOR_REQUIRED_FIELDS: Final[frozenset[str]] = frozenset(
    {"source", "id", "title", "description", "url", "skills"}
)
COLLECTOR_OPTIONAL_FIELDS: Final[frozenset[str]] = frozenset(
    {
        "posted_at",
        "job_type",
        "contractor_tier",
        "hourly_min",
        "hourly_max",
        "fixed_amount",
        "raw_id",
    }
)
COLLECTOR_ALLOWED_FIELDS: Final[frozenset[str]] = (
    COLLECTOR_REQUIRED_FIELDS | COLLECTOR_OPTIONAL_FIELDS
)
PRIVATE_UPSTREAM_FIELD_HINTS: Final[frozenset[str]] = frozenset(
    {
        "authorization",
        "bearer",
        "cipherText",
        "ciphertext",
        "cookie",
        "data",
        "errors",
        "extensions",
        "headers",
        "job",
        "proxy",
        "query",
        "session",
        "token",
        "variables",
        "visitor_gql_token",
    }
)


class RawRecordValidationError(ValueError):
    """Raised when a payload is not a collector-normalized job JSON object."""


@dataclass(frozen=True, slots=True)
class RawRecord:
    raw_record_id: str
    job_id: str
    run_id: str
    content_hash: str
    received_at: str
    payload_json: str


def initialize_raw_record_schema(conn: sqlite3.Connection) -> None:
    """Create the minimal schema needed to persist normalized raw records."""

    conn.execute("PRAGMA foreign_keys = ON")
    conn.executescript(
        """
        CREATE TABLE IF NOT EXISTS ingest_runs (
            run_id TEXT PRIMARY KEY,
            source_query TEXT NULL,
            input_path TEXT NULL,
            started_at TEXT NOT NULL,
            completed_at TEXT NULL,
            record_count INTEGER NOT NULL DEFAULT 0,
            status TEXT NOT NULL
        );

        CREATE TABLE IF NOT EXISTS raw_records (
            raw_record_id TEXT PRIMARY KEY,
            job_id TEXT NULL,
            run_id TEXT NOT NULL,
            content_hash TEXT NOT NULL,
            received_at TEXT NOT NULL,
            payload_json TEXT NOT NULL,
            FOREIGN KEY (run_id) REFERENCES ingest_runs(run_id)
        );

        CREATE INDEX IF NOT EXISTS idx_raw_records_content_hash
            ON raw_records(content_hash);
        CREATE INDEX IF NOT EXISTS idx_raw_records_run_id
            ON raw_records(run_id);
        """
    )


def insert_raw_record(
    conn: sqlite3.Connection,
    *,
    run_id: str,
    payload_json: str,
    raw_record_id: str | None = None,
    received_at: str | None = None,
) -> RawRecord:
    """Persist one normalized collector JSON object in ``raw_records``.

    ``payload_json`` is stored exactly as received after trimming JSONL line whitespace.
    Validation rejects upstream GraphQL envelopes, credential-bearing structures, and fields
    outside the current collector JSONL contract.
    """

    initialize_raw_record_schema(conn)
    normalized_payload = payload_json.strip()
    record = _parse_collector_payload(normalized_payload)
    validate_collector_payload(record)

    now = received_at or _utc_now()
    _ensure_ingest_run(conn, run_id=run_id, timestamp=now)

    job_id = str(record["id"])
    canonical_payload = _canonical_json(record)
    stored = RawRecord(
        raw_record_id=raw_record_id or str(uuid.uuid4()),
        job_id=job_id,
        run_id=run_id,
        content_hash=hashlib.sha256(canonical_payload.encode("utf-8")).hexdigest(),
        received_at=now,
        payload_json=normalized_payload,
    )
    conn.execute(
        """
        INSERT INTO raw_records (
            raw_record_id,
            job_id,
            run_id,
            content_hash,
            received_at,
            payload_json
        ) VALUES (?, ?, ?, ?, ?, ?)
        """,
        (
            stored.raw_record_id,
            stored.job_id,
            stored.run_id,
            stored.content_hash,
            stored.received_at,
            stored.payload_json,
        ),
    )
    return stored


def validate_collector_payload(record: Mapping[str, Any]) -> None:
    """Validate that ``record`` is the collector's normalized job contract only."""

    fields = frozenset(record)
    private_fields = fields & PRIVATE_UPSTREAM_FIELD_HINTS
    if private_fields:
        raise RawRecordValidationError(
            "raw_records cannot store upstream/private fields: " + ", ".join(sorted(private_fields))
        )

    missing = COLLECTOR_REQUIRED_FIELDS - fields
    if missing:
        raise RawRecordValidationError(
            "collector payload missing required fields: " + ", ".join(sorted(missing))
        )

    unknown_fields = fields - COLLECTOR_ALLOWED_FIELDS
    if unknown_fields:
        raise RawRecordValidationError(
            "collector payload contains non-contract fields: " + ", ".join(sorted(unknown_fields))
        )

    _require_text(record, "source")
    _require_text(record, "id")
    _require_text(record, "title")
    _require_text(record, "description")
    _require_text(record, "url")
    skills = record["skills"]
    if not isinstance(skills, list) or not all(isinstance(skill, str) for skill in skills):
        raise RawRecordValidationError("collector payload field skills must be a list of strings")

    for field in ("posted_at", "job_type", "contractor_tier", "raw_id"):
        value = record.get(field)
        if value is not None and not isinstance(value, str):
            raise RawRecordValidationError(
                f"collector payload field {field} must be string or null"
            )

    for field in ("hourly_min", "hourly_max", "fixed_amount"):
        value = record.get(field)
        if value is not None and not isinstance(value, int | float):
            raise RawRecordValidationError(
                f"collector payload field {field} must be number or null"
            )


def _parse_collector_payload(payload_json: str) -> dict[str, Any]:
    try:
        parsed = json.loads(payload_json)
    except json.JSONDecodeError as exc:
        raise RawRecordValidationError("payload_json must be valid JSON") from exc
    if not isinstance(parsed, dict):
        raise RawRecordValidationError("payload_json must be a JSON object")
    return parsed


def _ensure_ingest_run(conn: sqlite3.Connection, *, run_id: str, timestamp: str) -> None:
    conn.execute(
        """
        INSERT OR IGNORE INTO ingest_runs (run_id, started_at, status)
        VALUES (?, ?, ?)
        """,
        (run_id, timestamp, "in_progress"),
    )


def _require_text(record: Mapping[str, Any], field: str) -> None:
    if not isinstance(record[field], str) or not record[field]:
        raise RawRecordValidationError(
            f"collector payload field {field} must be a non-empty string"
        )


def _canonical_json(record: Mapping[str, Any]) -> str:
    return json.dumps(record, ensure_ascii=False, separators=(",", ":"), sort_keys=True)


def _utc_now() -> str:
    return datetime.now(UTC).replace(microsecond=0).isoformat().replace("+00:00", "Z")
