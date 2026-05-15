from __future__ import annotations

import sqlite3
from pathlib import Path

from tests.run_history_helpers import insert_success_run

from work_feed_mcp.db.schema import initialize_schema
from work_feed_mcp.repositories import run_history
from work_feed_mcp.repositories.run_history import RunTotals


def test_initialize_schema_creates_run_history_idempotently(tmp_path: Path) -> None:
    db = tmp_path / "work-feed.sqlite"
    connection = sqlite3.connect(db)
    try:
        initialize_schema(connection)
        initialize_schema(connection)
        tables = {
            row[0]
            for row in connection.execute("SELECT name FROM sqlite_master WHERE type='table'")
        }
        assert {"jobs", "job_skills", "collector_runs", "collector_run_results"} <= tables
    finally:
        connection.close()


def test_run_history_records_success_and_failure(tmp_path: Path) -> None:
    connection = sqlite3.connect(tmp_path / "work-feed.sqlite")
    connection.row_factory = sqlite3.Row
    try:
        initialize_schema(connection)
        insert_success_run(connection)
        latest = run_history.latest_run(connection)
        assert latest is not None
        assert latest["status"] == "success"
        assert latest["duration_seconds"] == 5
        assert run_history.recent_results(connection, run_id="run-1", limit=5)[0]["query"] is None

        run_history.create_run(
            connection,
            run_id="run-2",
            started_at="2026-05-14T00:01:00Z",
            trigger="scheduled",
            query_count=1,
        )
        run_history.finish_run_failure(
            connection,
            run_id="run-2",
            finished_at="2026-05-14T00:01:01Z",
            totals=RunTotals(),
            error_type="UpstreamBlockedError",
            redacted_error="blocked token=<redacted>",
        )
        latest = run_history.latest_run(connection)
        assert latest is not None
        assert latest["status"] == "failed"
        assert latest["redacted_error"] == "blocked token=<redacted>"
    finally:
        connection.close()
