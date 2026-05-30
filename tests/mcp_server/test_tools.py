from __future__ import annotations

import sqlite3
from pathlib import Path
from typing import Any

from work_feed_mcp.db.connection import connect_worker
from work_feed_mcp.mcp_server import tools
from work_feed_mcp.repositories import collector_control
from work_feed_mcp.runtime.config import RuntimeSettings


def test_mcp_control_tools_enqueue_commands(tmp_path: Path) -> None:
    db = tmp_path / "work-feed.sqlite"
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
    db = tmp_path / "work-feed.sqlite"
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
    db = tmp_path / "work-feed.sqlite"
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


def test_sqlite_errors_return_storage_error(monkeypatch, tmp_path: Path) -> None:  # type: ignore[no-untyped-def]
    def raise_storage_error(*_args: Any, **_kwargs: Any) -> dict[str, Any]:
        raise sqlite3.OperationalError("database is locked token=secret")

    monkeypatch.setattr(tools, "query_jobs_recent", raise_storage_error)

    result = tools.jobs_recent(settings=RuntimeSettings(db_path=str(tmp_path / "work-feed.sqlite")))

    assert result == {
        "ok": False,
        "error": "storage_error",
        "message": "runtime storage unavailable",
    }


def test_unexpected_errors_return_redacted_internal_error(
    monkeypatch,
    tmp_path: Path,
) -> None:  # type: ignore[no-untyped-def]
    def raise_internal_error(*_args: Any, **_kwargs: Any) -> dict[str, Any]:
        raise RuntimeError("unexpected token=secret diagnostic")

    monkeypatch.setattr(tools, "query_jobs_recent", raise_internal_error)

    result = tools.jobs_recent(settings=RuntimeSettings(db_path=str(tmp_path / "work-feed.sqlite")))

    assert result["ok"] is False
    assert result["error"] == "internal_error"
    assert result["error_type"] == "RuntimeError"
    assert result["message"] == "unexpected token=<redacted> diagnostic"
    assert "secret" not in result["message"]
