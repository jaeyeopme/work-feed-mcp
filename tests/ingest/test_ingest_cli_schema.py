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


def test_ingest_cli_file_input_writes_jobs_and_skills_only(tmp_path: Path, capsys) -> None:  # type: ignore[no-untyped-def]
    jsonl = tmp_path / "jobs.jsonl"
    db = tmp_path / "upwork.sqlite"
    _write_jsonl(jsonl, [_record(), _record("~022222", title="React UI")])

    assert main(["--db", str(db), "--input", str(jsonl), "--query", "python"]) == 0
    payload = json.loads(capsys.readouterr().out)

    assert payload["seen_count"] == 2
    assert payload["inserted_count"] == 2
    assert payload["skipped_count"] == 0
    assert len(payload["new_jobs"]) == 2

    connection = sqlite3.connect(db)
    assert connection.execute("SELECT COUNT(*) FROM jobs").fetchone()[0] == 2
    assert (
        connection.execute("SELECT COUNT(*) FROM job_skills WHERE skill = 'python'").fetchone()[0]
        == 2
    )
    tables = {
        row[0] for row in connection.execute("SELECT name FROM sqlite_master WHERE type = 'table'")
    }
    assert {"jobs", "job_skills", "collector_runs", "collector_run_results"} <= tables
    assert "raw_payloads" not in tables


def test_repeated_ingest_skips_existing_jobs(tmp_path: Path, capsys) -> None:  # type: ignore[no-untyped-def]
    jsonl = tmp_path / "jobs.jsonl"
    db = tmp_path / "upwork.sqlite"
    _write_jsonl(jsonl, [_record()])

    assert main(["--db", str(db), "--input", str(jsonl)]) == 0
    capsys.readouterr()
    assert main(["--db", str(db), "--input", str(jsonl)]) == 0
    payload = json.loads(capsys.readouterr().out)

    assert payload["seen_count"] == 1
    assert payload["inserted_count"] == 0
    assert payload["skipped_count"] == 1
    assert payload["new_jobs"] == []
    connection = sqlite3.connect(db)
    assert connection.execute("SELECT COUNT(*) FROM jobs").fetchone()[0] == 1


def test_schema_uses_jobs_only_indexes(tmp_path: Path) -> None:
    jsonl = tmp_path / "jobs.jsonl"
    db = tmp_path / "upwork.sqlite"
    _write_jsonl(jsonl, [_record()])
    assert main(["--db", str(db), "--input", str(jsonl)]) == 0

    connection = sqlite3.connect(db)
    indexes = {
        row[0] for row in connection.execute("SELECT name FROM sqlite_master WHERE type = 'index'")
    }
    assert {"idx_jobs_content_hash", "idx_jobs_first_seen_at", "idx_job_skills_skill"} <= indexes
    columns = {row[1] for row in connection.execute("PRAGMA table_info(jobs)")}
    assert "first_seen_at" in columns
    assert "created_at" in columns
    assert "last_seen_at" not in columns
