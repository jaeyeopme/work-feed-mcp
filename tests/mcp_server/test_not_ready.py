from __future__ import annotations

import sqlite3
from pathlib import Path

from upwork_app.db.connection import connect_worker
from upwork_app.mcp_server import tools
from upwork_app.runtime.config import RuntimeSettings


def test_missing_db_returns_not_ready(tmp_path: Path) -> None:
    settings = RuntimeSettings(db_path=str(tmp_path / "missing.sqlite"))
    assert tools.jobs_recent(settings=settings)["reason"] == "db_missing"
    assert not Path(settings.db_path).exists()


def test_schema_missing_returns_not_ready_without_initializing(tmp_path: Path) -> None:
    db = tmp_path / "bare.sqlite"
    sqlite3.connect(db).close()
    settings = RuntimeSettings(db_path=str(db))
    result = tools.collector_status(settings=settings)
    assert result["reason"] == "schema_missing"
    connection = sqlite3.connect(db)
    try:
        assert list(connection.execute("SELECT name FROM sqlite_master WHERE type = 'table'")) == []
    finally:
        connection.close()


def test_empty_schema_returns_ok_empty(tmp_path: Path) -> None:
    db = tmp_path / "upwork.sqlite"
    connection = connect_worker(str(db))
    connection.close()
    settings = RuntimeSettings(db_path=str(db))
    result = tools.jobs_recent(settings=settings)
    assert result["ok"] is True
    assert result["status"] == "empty"
    assert result["rows"] == []
