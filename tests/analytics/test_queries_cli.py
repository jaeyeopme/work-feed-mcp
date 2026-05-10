from __future__ import annotations

import json
import sqlite3
from pathlib import Path

from upwork_app.cli.analytics import main
from upwork_app.repositories.analytics import budgets, jobs, runs, skills, summary


def _seed_db(path: Path) -> None:
    connection = sqlite3.connect(path)
    connection.executescript(
        """
        CREATE TABLE ingest_runs (
          run_id TEXT PRIMARY KEY,
          source_query TEXT NULL,
          input_path TEXT NULL,
          started_at TEXT NOT NULL,
          completed_at TEXT NULL,
          record_count INTEGER NOT NULL DEFAULT 0,
          status TEXT NOT NULL
        );
        CREATE TABLE jobs (
          job_id TEXT PRIMARY KEY,
          source TEXT NOT NULL,
          title TEXT NOT NULL,
          description TEXT NULL,
          url TEXT NULL,
          posted_at TEXT NULL,
          job_type TEXT NULL,
          contractor_tier TEXT NULL,
          hourly_min REAL NULL,
          hourly_max REAL NULL,
          fixed_amount REAL NULL,
          raw_id TEXT NULL,
          content_hash TEXT NOT NULL,
          first_seen_at TEXT NOT NULL,
          last_seen_at TEXT NOT NULL
        );
        CREATE TABLE job_skills (job_id TEXT NOT NULL, skill TEXT NOT NULL);
        CREATE TABLE job_observations (
          observation_id TEXT PRIMARY KEY,
          job_id TEXT NOT NULL,
          run_id TEXT NOT NULL,
          source_query TEXT NULL,
          observed_at TEXT NOT NULL,
          content_hash TEXT NOT NULL
        );
        CREATE TABLE raw_records (
          raw_record_id TEXT PRIMARY KEY,
          job_id TEXT NULL,
          run_id TEXT NOT NULL,
          content_hash TEXT NOT NULL,
          received_at TEXT NOT NULL,
          payload_json TEXT NOT NULL
        );
        """
    )
    connection.execute(
        "INSERT INTO ingest_runs VALUES (?, ?, ?, ?, ?, ?, ?)",
        (
            "run-1",
            "python",
            "jobs.jsonl",
            "2026-05-10T00:00:00Z",
            "2026-05-10T00:00:01Z",
            2,
            "completed",
        ),
    )
    connection.executemany(
        """
        INSERT INTO jobs (
          job_id, source, title, description, url, posted_at, job_type, contractor_tier,
          hourly_min, hourly_max, fixed_amount, raw_id, content_hash, first_seen_at, last_seen_at
        ) VALUES (?, 'upwork', ?, ?, ?, NULL, ?, NULL, ?, ?, ?, NULL, ?, ?, ?)
        """,
        [
            (
                "job-1",
                "Python data pipeline",
                "Build SQLite ingest",
                "https://example.test/1",
                "hourly",
                40.0,
                70.0,
                None,
                "hash-1",
                "2026-05-10T00:00:00Z",
                "2026-05-10T00:00:00Z",
            ),
            (
                "job-2",
                "Frontend fix",
                "React UI",
                "https://example.test/2",
                "fixed",
                None,
                None,
                500.0,
                "hash-2",
                "2026-05-10T00:00:00Z",
                "2026-05-10T00:00:00Z",
            ),
        ],
    )
    connection.executemany(
        "INSERT INTO job_skills VALUES (?, ?)",
        [("job-1", "python"), ("job-1", "sqlite"), ("job-2", "react")],
    )
    connection.executemany(
        "INSERT INTO job_observations VALUES (?, ?, ?, ?, ?, ?)",
        [
            ("obs-1", "job-1", "run-1", "python", "2026-05-10T00:00:00Z", "hash-1"),
            ("obs-2", "job-2", "run-1", "python", "2026-05-10T00:00:00Z", "hash-2"),
        ],
    )
    connection.executemany(
        "INSERT INTO raw_records VALUES (?, ?, ?, ?, ?, ?)",
        [("raw-1", "job-1", "run-1", "hash-1", "2026-05-10T00:00:00Z", "{}")],
    )
    connection.commit()
    connection.close()


def test_query_helpers_return_basic_analytics(tmp_path: Path) -> None:
    db = tmp_path / "upwork.sqlite"
    _seed_db(db)
    connection = sqlite3.connect(db)
    connection.row_factory = sqlite3.Row

    assert summary(connection).rows == (
        {"jobs": 2, "runs": 1, "observations": 2, "raw_records": 1},
    )
    assert skills(connection).rows[0] == {"skill": "python", "count": 1}
    assert jobs(connection, skill="Python").rows[0]["job_id"] == "job-1"
    assert {row["budget_type"] for row in budgets(connection).rows} == {"fixed", "hourly"}
    assert runs(connection).rows[0]["run_id"] == "run-1"


def test_cli_outputs_json_and_reads_sqlite_only(tmp_path: Path, capsys) -> None:
    db = tmp_path / "upwork.sqlite"
    _seed_db(db)

    assert main(["skills", "--db", str(db)]) == 0
    output = json.loads(capsys.readouterr().out)

    assert output["query"] == "skills"
    assert {row["skill"] for row in output["rows"]} == {"python", "sqlite", "react"}
