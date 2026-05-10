from __future__ import annotations

import json
import sqlite3
from pathlib import Path

from upwork_app.cli.ingest import main


def _record(job_id: str = "~021111", *, title: str = "Python data pipeline") -> dict[str, object]:
    return {
        "source": "upwork",
        "id": job_id,
        "title": title,
        "description": "Build ingestion pipelines",
        "url": f"https://www.upwork.com/jobs/{job_id}",
        "skills": ["Python", "SQLite", "python"],
        "posted_at": None,
        "job_type": "hourly",
        "contractor_tier": None,
        "hourly_min": 40,
        "hourly_max": 70,
        "fixed_amount": None,
        "raw_id": job_id.removeprefix("~"),
    }


def _write_jsonl(path: Path, records: list[dict[str, object]]) -> None:
    path.write_text("".join(json.dumps(record) + "\n" for record in records), encoding="utf-8")


def test_ingest_cli_file_input_writes_schema_rows_and_raw_records(tmp_path: Path) -> None:
    jsonl = tmp_path / "jobs.jsonl"
    db = tmp_path / "upwork.sqlite"
    _write_jsonl(jsonl, [_record(), _record("~022222", title="React UI")])

    assert main(["--db", str(db), "--input", str(jsonl), "--query", "python"]) == 0

    connection = sqlite3.connect(db)
    assert connection.execute("SELECT COUNT(*) FROM ingest_runs").fetchone()[0] == 1
    assert connection.execute("SELECT COUNT(*) FROM jobs").fetchone()[0] == 2
    assert (
        connection.execute("SELECT COUNT(*) FROM job_skills WHERE skill = 'python'").fetchone()[0]
        == 2
    )
    assert connection.execute("SELECT COUNT(*) FROM job_observations").fetchone()[0] == 2
    assert connection.execute("SELECT COUNT(*) FROM raw_records").fetchone()[0] == 2
    assert connection.execute("SELECT source_query FROM ingest_runs").fetchone()[0] == "python"


def test_repeated_ingest_is_idempotent_for_jobs_but_records_observations(tmp_path: Path) -> None:
    jsonl = tmp_path / "jobs.jsonl"
    db = tmp_path / "upwork.sqlite"
    _write_jsonl(jsonl, [_record()])

    assert main(["--db", str(db), "--input", str(jsonl), "--run-id", "run-a"]) == 0
    assert main(["--db", str(db), "--input", str(jsonl), "--run-id", "run-b"]) == 0

    connection = sqlite3.connect(db)
    assert connection.execute("SELECT COUNT(*) FROM jobs").fetchone()[0] == 1
    assert connection.execute("SELECT COUNT(*) FROM ingest_runs").fetchone()[0] == 2
    assert connection.execute("SELECT COUNT(*) FROM job_observations").fetchone()[0] == 2
    first_seen, last_seen = connection.execute(
        "SELECT first_seen_at, last_seen_at FROM jobs WHERE job_id = '~021111'"
    ).fetchone()
    assert first_seen <= last_seen


def test_schema_uses_explicit_keys_indexes_and_text_json_payload(tmp_path: Path) -> None:
    jsonl = tmp_path / "jobs.jsonl"
    db = tmp_path / "upwork.sqlite"
    _write_jsonl(jsonl, [_record()])
    assert main(["--db", str(db), "--input", str(jsonl)]) == 0

    connection = sqlite3.connect(db)
    tables = {
        row[0] for row in connection.execute("SELECT name FROM sqlite_master WHERE type = 'table'")
    }
    assert {"ingest_runs", "jobs", "job_skills", "job_observations", "raw_records"} <= tables
    indexes = {
        row[0] for row in connection.execute("SELECT name FROM sqlite_master WHERE type = 'index'")
    }
    assert {
        "idx_jobs_content_hash",
        "idx_job_skills_skill",
        "idx_job_observations_run_id",
        "idx_job_observations_source_query",
        "idx_raw_records_content_hash",
    } <= indexes
    raw_columns = {row[1]: row[2] for row in connection.execute("PRAGMA table_info(raw_records)")}
    assert raw_columns["payload_json"].upper() == "TEXT"
