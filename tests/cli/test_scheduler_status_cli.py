from __future__ import annotations

import json
import sqlite3
from pathlib import Path

from tests.run_history_helpers import insert_success_run

from upwork_app.cli import __main__, scheduler_status
from upwork_app.db.schema import initialize_schema


def test_scheduler_status_empty_db_returns_agent_readable_json(
    tmp_path: Path,
    capsys,
) -> None:  # type: ignore[no-untyped-def]
    db = tmp_path / "upwork.sqlite"
    connection = sqlite3.connect(db)
    initialize_schema(connection)
    connection.close()

    assert scheduler_status.main(["--db", str(db)]) == 0
    payload = json.loads(capsys.readouterr().out)

    assert payload["query"] == "scheduler-status"
    assert payload["last_run"] is None
    assert payload["recent_runs"] == []
    assert payload["recent_results"] == []


def test_scheduler_status_outputs_latest_run_and_results(tmp_path: Path, capsys) -> None:  # type: ignore[no-untyped-def]
    db = tmp_path / "upwork.sqlite"
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


def test_scheduler_status_missing_db_returns_usage_error(tmp_path: Path, capsys) -> None:  # type: ignore[no-untyped-def]
    assert scheduler_status.main(["--db", str(tmp_path / "missing.sqlite")]) == 2
    assert "SQLite database path does not exist" in capsys.readouterr().err
