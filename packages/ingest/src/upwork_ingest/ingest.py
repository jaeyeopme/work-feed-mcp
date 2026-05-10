"""Compatibility shim for JSONL-to-SQLite ingest."""

from upwork_app.services.ingestion import (
    IngestResult,
    ingest_jsonl,
    ingest_records,
    load_records,
    read_jsonl,
    utc_now,
)

__all__ = [
    "IngestResult",
    "ingest_jsonl",
    "ingest_records",
    "load_records",
    "read_jsonl",
    "utc_now",
]
