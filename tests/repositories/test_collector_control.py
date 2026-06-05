from __future__ import annotations

from pathlib import Path

import pytest

from work_feed_mcp.db.connection import connect_worker
from work_feed_mcp.repositories import collector_control


def test_schema_contains_control_tables_and_indexes(tmp_path: Path) -> None:
    connection = connect_worker(str(tmp_path / "work-feed.sqlite"))
    try:
        names = {
            str(row[0])
            for row in connection.execute(
                "SELECT name FROM sqlite_master WHERE type IN ('table', 'index')"
            )
        }
    finally:
        connection.close()
    assert "collector_config" in names
    assert "collector_commands" in names
    assert "idx_collector_commands_status_created_at" in names
    assert "idx_collector_commands_created_at" in names
    assert "idx_collector_run_results_run_started_id" in names
    assert "idx_collector_run_results_started_id" in names
    assert "idx_collector_runs_started_run_id" in names
    assert "idx_jobs_first_seen_job_id" in names


def test_seed_config_preserves_existing_values(tmp_path: Path) -> None:
    connection = connect_worker(str(tmp_path / "work-feed.sqlite"))
    try:
        collector_control.seed_config(connection, {"interval_seconds": 3600, "page_size": 50})
        collector_control.update_config(connection, {"interval_seconds": 120}, updated_by="mcp")
        collector_control.seed_config(connection, {"interval_seconds": 999, "max_pages": 5})
        config = collector_control.get_config(connection)
    finally:
        connection.close()
    assert config["interval_seconds"] == 120
    assert config["max_pages"] == 5


def test_update_config_rejects_unsupported_keys(tmp_path: Path) -> None:
    connection = connect_worker(str(tmp_path / "work-feed.sqlite"))
    try:
        with pytest.raises(ValueError):
            collector_control.update_config(connection, {"live": False})
    finally:
        connection.close()


def test_command_lifecycle(tmp_path: Path) -> None:
    connection = connect_worker(str(tmp_path / "work-feed.sqlite"))
    try:
        queued = collector_control.enqueue_command(connection, "run_once", command_id="cmd-1")
        assert queued == {"ok": True, "command_id": "cmd-1", "status": "queued"}
        command = collector_control.next_queued_command(connection)
        assert command is not None
        assert command["command_type"] == "run_once"
        collector_control.mark_running(connection, "cmd-1")
        collector_control.mark_applied(connection, "cmd-1", result={"done": True})
        status = collector_control.command_status(connection, "cmd-1")
    finally:
        connection.close()
    assert status is not None
    assert status["status"] == "applied"
    assert status["result"] == {"done": True}


def test_failed_command_status_returns_json_safe_error_details(tmp_path: Path) -> None:
    connection = connect_worker(str(tmp_path / "work-feed.sqlite"))
    try:
        collector_control.enqueue_command(connection, "run_once", command_id="cmd-fail")
        collector_control.mark_running(connection, "cmd-fail")
        collector_control.mark_failed(
            connection,
            "cmd-fail",
            error_type="UpstreamBlockedError",
            redacted_error="blocked token=<redacted>",
        )
        status = collector_control.command_status(connection, "cmd-fail")
    finally:
        connection.close()

    assert status is not None
    assert status["status"] == "failed"
    assert status["error_type"] == "UpstreamBlockedError"
    assert status["redacted_error"] == "blocked token=<redacted>"
    assert "secret" not in str(status["redacted_error"])
