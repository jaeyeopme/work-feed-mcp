from __future__ import annotations

import sqlite3
from pathlib import Path

from work_feed_mcp.db.schema import SCHEMA_VERSION, initialize_schema
from work_feed_mcp.services.scheduler_status import scheduler_status


def _table_names(db: Path) -> list[str]:
    connection = sqlite3.connect(db)
    try:
        return [
            str(row[0])
            for row in connection.execute(
                "SELECT name FROM sqlite_master WHERE type = 'table' ORDER BY name"
            )
        ]
    finally:
        connection.close()


def test_missing_database_returns_not_ready_without_creating_file(tmp_path: Path) -> None:
    db = tmp_path / "missing.sqlite"

    result = scheduler_status(str(db))

    assert result["ok"] is False
    assert result["error"] == "not_ready"
    assert result["reason"] == "db_missing"
    assert result["details"] == "database file does not exist"
    assert not db.exists()


def test_schema_missing_returns_not_ready_without_initializing_tables(tmp_path: Path) -> None:
    db = tmp_path / "bare.sqlite"
    sqlite3.connect(db).close()

    result = scheduler_status(str(db))

    assert result["ok"] is False
    assert result["error"] == "not_ready"
    assert result["reason"] == "schema_missing"
    assert result["details"] == "runtime schema is missing required tables"
    assert _table_names(db) == []


def test_unsupported_schema_returns_not_ready_without_downgrade(tmp_path: Path) -> None:
    db = tmp_path / "newer.sqlite"
    connection = sqlite3.connect(db)
    try:
        connection.execute(f"PRAGMA user_version = {SCHEMA_VERSION + 1}")
        connection.commit()
    finally:
        connection.close()

    result = scheduler_status(str(db))

    assert result["ok"] is False
    assert result["error"] == "not_ready"
    assert result["reason"] == "unsupported_schema"
    assert (
        result["details"] == "database schema version is newer than this work-feed build supports"
    )
    assert _table_names(db) == []
    connection = sqlite3.connect(db)
    try:
        assert int(connection.execute("PRAGMA user_version").fetchone()[0]) == SCHEMA_VERSION + 1
    finally:
        connection.close()


def test_ready_database_returns_status_without_writing_schema(tmp_path: Path) -> None:
    db = tmp_path / "ready.sqlite"
    connection = sqlite3.connect(db)
    try:
        initialize_schema(connection)
        connection.commit()
    finally:
        connection.close()

    result = scheduler_status(str(db))

    assert result["ok"] is True
    assert result["query"] == "scheduler-status"
    assert result["last_run"] is None
    assert result["recent_runs"] == []
    assert result["recent_results"] == []
