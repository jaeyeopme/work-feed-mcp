from __future__ import annotations

import sqlite3
from contextlib import closing
from io import StringIO
from pathlib import Path

import pytest

from work_feed_mcp.core.errors import ValidationError
from work_feed_mcp.domain.collector_record import CollectorRecord, validate_payload
from work_feed_mcp.services import ingestion


def _record(job_id: str = "~021111") -> CollectorRecord:
    return validate_payload(
        {
            "source": "upwork",
            "id": job_id,
            "title": "Python data pipeline",
            "description": "Build ingestion pipelines",
            "url": f"https://www.upwork.com/jobs/{job_id}",
            "skills": ["Python", "SQLite"],
            "posted_at": None,
            "job_type": "hourly",
            "contractor_tier": None,
            "hourly_min": 40,
            "hourly_max": 70,
            "fixed_amount": None,
            "raw_id": job_id.removeprefix("~"),
        }
    )


def test_read_jsonl_reports_malformed_json_line_number() -> None:
    stream = StringIO(f"{_record().payload_json}\n{{bad json}}\n")

    with pytest.raises(ValidationError, match="malformed JSONL at line 2"):
        ingestion.read_jsonl(stream)


def test_read_jsonl_reports_invalid_record_line_number() -> None:
    stream = StringIO('{"source": "upwork"}\n')

    with pytest.raises(ValidationError, match="invalid collector record at line 1"):
        ingestion.read_jsonl(stream)


def test_ingest_records_rolls_back_job_insert_when_persistence_fails(
    tmp_path: Path, monkeypatch: pytest.MonkeyPatch
) -> None:
    db = tmp_path / "work-feed.sqlite"

    def fail_insert_skills(connection: sqlite3.Connection, record: CollectorRecord) -> None:
        raise RuntimeError("skill insert failed")

    monkeypatch.setattr(ingestion.ingestion_repository, "insert_skills", fail_insert_skills)

    with pytest.raises(RuntimeError, match="skill insert failed"):
        ingestion.ingest_records(
            [_record()],
            db_path=str(db),
            input_path=None,
            source_query="python",
        )

    with closing(sqlite3.connect(db)) as connection:
        assert connection.execute("SELECT COUNT(*) FROM jobs").fetchone()[0] == 0
