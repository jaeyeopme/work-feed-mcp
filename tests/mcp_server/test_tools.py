from __future__ import annotations

from pathlib import Path

from upwork_app.db.connection import connect_worker
from upwork_app.mcp_server import tools
from upwork_app.repositories import collector_control
from upwork_app.runtime.config import RuntimeSettings


def test_mcp_control_tools_enqueue_commands(tmp_path: Path) -> None:
    db = tmp_path / "upwork.sqlite"
    with connect_worker(str(db)) as connection:
        collector_control.seed_config(
            connection, RuntimeSettings(db_path=str(db)).persisted_defaults()
        )
        connection.commit()
    settings = RuntimeSettings(db_path=str(db))

    result = tools.collector_run_once(settings=settings)
    assert result["ok"] is True
    assert result["status"] == "queued"
    status = tools.collector_command_status(command_id=str(result["command_id"]), settings=settings)
    assert status["ok"] is True
    assert status["command"]["command_type"] == "run_once"


def test_config_update_enqueues_update_command(tmp_path: Path) -> None:
    db = tmp_path / "upwork.sqlite"
    with connect_worker(str(db)) as connection:
        collector_control.seed_config(
            connection, RuntimeSettings(db_path=str(db)).persisted_defaults()
        )
        connection.commit()
    settings = RuntimeSettings(db_path=str(db))

    result = tools.config_update(updates={"page_size": 25}, settings=settings)
    assert result["ok"] is True
    assert result["status"] == "queued"

    status = tools.collector_command_status(command_id=str(result["command_id"]), settings=settings)
    assert status["ok"] is True
    assert status["command"]["command_type"] == "update_config"
    assert status["command"]["payload"] == {"updates": {"page_size": 25}}


def test_invalid_config_update_returns_json_safe_error(tmp_path: Path) -> None:
    db = tmp_path / "upwork.sqlite"
    with connect_worker(str(db)) as connection:
        collector_control.seed_config(
            connection, RuntimeSettings(db_path=str(db)).persisted_defaults()
        )
        connection.commit()
    settings = RuntimeSettings(db_path=str(db))

    result = tools.config_update(updates={"live": False}, settings=settings)
    assert result == {
        "ok": False,
        "error": "invalid_request",
        "message": "unsupported config keys: live",
    }
