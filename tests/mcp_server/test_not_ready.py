from __future__ import annotations

import sqlite3
from pathlib import Path

from work_feed_mcp.db.connection import connect_worker
from work_feed_mcp.mcp_server import tools
from work_feed_mcp.runtime.config import RuntimeSettings


def _create_db_with_user_version(tmp_path: Path, filename: str, version: int) -> Path:
    db = tmp_path / filename
    connection = sqlite3.connect(db)
    try:
        connection.execute(f"PRAGMA user_version = {version}")
        connection.commit()
    finally:
        connection.close()
    return db


def _assert_db_has_user_version_only(db: Path, version: int) -> None:
    connection = sqlite3.connect(db)
    try:
        assert int(connection.execute("PRAGMA user_version").fetchone()[0]) == version
        assert list(connection.execute("SELECT name FROM sqlite_master WHERE type = 'table'")) == []
    finally:
        connection.close()


def test_missing_db_returns_not_ready(tmp_path: Path) -> None:
    settings = RuntimeSettings(db_path=str(tmp_path / "missing.sqlite"))
    result = tools.jobs_recent(settings=settings)
    assert result["reason"] == "db_missing"
    assert result["details"] == "database file does not exist"
    assert not Path(settings.db_path).exists()


def test_schema_missing_returns_not_ready_without_initializing(tmp_path: Path) -> None:
    db = tmp_path / "bare.sqlite"
    sqlite3.connect(db).close()
    settings = RuntimeSettings(db_path=str(db))
    result = tools.collector_status(settings=settings)
    assert result["reason"] == "schema_missing"
    assert result["details"] == "runtime schema is missing required tables"
    connection = sqlite3.connect(db)
    try:
        assert list(connection.execute("SELECT name FROM sqlite_master WHERE type = 'table'")) == []
    finally:
        connection.close()


def test_empty_schema_returns_ok_empty(tmp_path: Path) -> None:
    db = tmp_path / "work-feed.sqlite"
    connection = connect_worker(str(db))
    connection.close()
    settings = RuntimeSettings(db_path=str(db))
    result = tools.jobs_recent(settings=settings)
    assert result["ok"] is True
    assert result["status"] == "empty"
    assert result["rows"] == []


def test_newer_schema_returns_not_ready_without_downgrade(tmp_path: Path) -> None:
    db = _create_db_with_user_version(tmp_path, "newer.sqlite", 999)

    settings = RuntimeSettings(db_path=str(db))
    result = tools.jobs_recent(settings=settings)
    assert result["reason"] == "unsupported_schema"
    assert (
        result["details"] == "database schema version is newer than this work-feed build supports"
    )
    assert result["next_action"] == "upgrade work-feed or migrate the database"

    _assert_db_has_user_version_only(db, 999)


def test_newer_schema_control_tool_returns_not_ready_without_downgrade(tmp_path: Path) -> None:
    db = _create_db_with_user_version(tmp_path, "newer-control.sqlite", 999)

    settings = RuntimeSettings(db_path=str(db))
    result = tools.collector_run_once(settings=settings)
    assert result["reason"] == "unsupported_schema"
    assert (
        result["details"] == "database schema version is newer than this work-feed build supports"
    )
    assert result["next_action"] == "upgrade work-feed or migrate the database"

    _assert_db_has_user_version_only(db, 999)
