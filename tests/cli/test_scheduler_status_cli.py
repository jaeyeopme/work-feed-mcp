from __future__ import annotations

import json
import sqlite3
from pathlib import Path

from tests.run_history_helpers import insert_success_run

from work_feed_mcp.cli import __main__, scheduler_status
from work_feed_mcp.db.schema import SCHEMA_VERSION, initialize_schema


def test_scheduler_status_empty_db_returns_agent_readable_json(
    tmp_path: Path,
    capsys,
) -> None:  # type: ignore[no-untyped-def]
    db = tmp_path / "work-feed.sqlite"
    connection = sqlite3.connect(db)
    initialize_schema(connection)
    connection.close()

    assert scheduler_status.main(["--db", str(db)]) == 0
    payload = json.loads(capsys.readouterr().out)

    assert payload["ok"] is True
    assert payload["query"] == "scheduler-status"
    assert payload["last_run"] is None
    assert payload["recent_runs"] == []
    assert payload["recent_results"] == []


def test_scheduler_status_outputs_latest_run_and_results(tmp_path: Path, capsys) -> None:  # type: ignore[no-untyped-def]
    db = tmp_path / "work-feed.sqlite"
    connection = sqlite3.connect(db)
    connection.row_factory = sqlite3.Row
    initialize_schema(connection)
    insert_success_run(
        connection,
        finished_at="2026-05-14T00:00:10Z",
        inserted=5,
        skipped=45,
    )
    connection.commit()
    connection.close()

    assert __main__.main(["scheduler-status", "--db", str(db), "--limit", "1"]) == 0
    payload = json.loads(capsys.readouterr().out)

    assert payload["last_run"]["run_id"] == "run-1"
    assert payload["last_run"]["duration_seconds"] == 10
    assert payload["recent_results"][0]["query"] is None
    assert payload["recent_results"][0]["inserted_count"] == 5


def test_scheduler_status_missing_db_returns_not_ready_json(tmp_path: Path, capsys) -> None:  # type: ignore[no-untyped-def]
    assert scheduler_status.main(["--db", str(tmp_path / "missing.sqlite")]) == 2
    captured = capsys.readouterr()
    payload = json.loads(captured.out)
    assert captured.err == ""
    assert payload["ok"] is False
    assert payload["error"] == "not_ready"
    assert payload["reason"] == "db_missing"
    assert payload["details"] == "database file does not exist"


def test_scheduler_status_schema_missing_returns_not_ready_json(
    tmp_path: Path,
    capsys,
) -> None:  # type: ignore[no-untyped-def]
    db = tmp_path / "bare.sqlite"
    sqlite3.connect(db).close()

    assert scheduler_status.main(["--db", str(db)]) == 2
    payload = json.loads(capsys.readouterr().out)
    assert payload["error"] == "not_ready"
    assert payload["reason"] == "schema_missing"
    assert payload["details"] == "runtime schema is missing required tables"

    connection = sqlite3.connect(db)
    try:
        assert list(connection.execute("SELECT name FROM sqlite_master WHERE type = 'table'")) == []
    finally:
        connection.close()


def test_scheduler_status_unsupported_schema_returns_not_ready_json(
    tmp_path: Path,
    capsys,
) -> None:  # type: ignore[no-untyped-def]
    db = tmp_path / "newer.sqlite"
    connection = sqlite3.connect(db)
    try:
        connection.execute(f"PRAGMA user_version = {SCHEMA_VERSION + 1}")
        connection.commit()
    finally:
        connection.close()

    assert scheduler_status.main(["--db", str(db)]) == 2
    payload = json.loads(capsys.readouterr().out)
    assert payload["error"] == "not_ready"
    assert payload["reason"] == "unsupported_schema"
    assert (
        payload["details"] == "database schema version is newer than this work-feed build supports"
    )

    connection = sqlite3.connect(db)
    try:
        assert int(connection.execute("PRAGMA user_version").fetchone()[0]) == SCHEMA_VERSION + 1
        assert list(connection.execute("SELECT name FROM sqlite_master WHERE type = 'table'")) == []
    finally:
        connection.close()
