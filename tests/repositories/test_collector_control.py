from __future__ import annotations

from pathlib import Path

import pytest

from upwork_app.db.connection import connect_worker
from upwork_app.repositories import collector_control


def test_schema_contains_control_tables_and_indexes(tmp_path: Path) -> None:
    connection = connect_worker(str(tmp_path / "upwork.sqlite"))
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


def test_seed_config_preserves_existing_values(tmp_path: Path) -> None:
    connection = connect_worker(str(tmp_path / "upwork.sqlite"))
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
    connection = connect_worker(str(tmp_path / "upwork.sqlite"))
    try:
        with pytest.raises(ValueError):
            collector_control.update_config(connection, {"live": False})
    finally:
        connection.close()


def test_command_lifecycle(tmp_path: Path) -> None:
    connection = connect_worker(str(tmp_path / "upwork.sqlite"))
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
