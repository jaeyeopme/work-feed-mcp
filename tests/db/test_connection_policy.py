from __future__ import annotations

import sqlite3
from pathlib import Path

import pytest

from work_feed_mcp.db.connection import connect_control, connect_readonly, connect_worker
from work_feed_mcp.db.schema import SCHEMA_VERSION, UnsupportedSchemaVersionError, initialize_schema
from work_feed_mcp.services.collector_control import NotReadyError
from work_feed_mcp.services.run_status import run_status


def test_worker_connection_initializes_schema_and_pragmas(tmp_path: Path) -> None:
    db = tmp_path / "work-feed.sqlite"
    connection = connect_worker(str(db))
    try:
        journal_mode = str(connection.execute("PRAGMA journal_mode").fetchone()[0]).lower()
        busy_timeout = int(connection.execute("PRAGMA busy_timeout").fetchone()[0])
        foreign_keys = int(connection.execute("PRAGMA foreign_keys").fetchone()[0])
        synchronous = int(connection.execute("PRAGMA synchronous").fetchone()[0])
        schema_version = int(connection.execute("PRAGMA user_version").fetchone()[0])
        tables = {
            str(row[0])
            for row in connection.execute("SELECT name FROM sqlite_master WHERE type = 'table'")
        }
    finally:
        connection.close()

    assert journal_mode == "wal"
    assert busy_timeout == 10_000
    assert foreign_keys == 1
    assert synchronous == 1
    assert schema_version == SCHEMA_VERSION
    assert {"collector_config", "collector_commands", "jobs", "collector_runs"} <= tables


def test_readonly_connection_does_not_create_missing_database(tmp_path: Path) -> None:
    db = tmp_path / "missing.sqlite"
    with pytest.raises(sqlite3.OperationalError):
        connect_readonly(str(db))
    assert not db.exists()


def test_control_connection_does_not_create_missing_database(tmp_path: Path) -> None:
    db = tmp_path / "missing.sqlite"
    with pytest.raises(sqlite3.OperationalError):
        connect_control(str(db))
    assert not db.exists()


def test_run_status_read_path_does_not_initialize_schema(tmp_path: Path) -> None:
    db = tmp_path / "bare.sqlite"
    sqlite3.connect(db).close()
    with pytest.raises(NotReadyError) as exc_info:
        run_status(str(db))
    assert exc_info.value.reason == "schema_missing"
    connection = sqlite3.connect(db)
    try:
        tables = list(connection.execute("SELECT name FROM sqlite_master WHERE type = 'table'"))
    finally:
        connection.close()
    assert tables == []


def test_initialize_schema_rejects_newer_database_version(tmp_path: Path) -> None:
    db = tmp_path / "newer.sqlite"
    connection = sqlite3.connect(db)
    try:
        connection.execute(f"PRAGMA user_version = {SCHEMA_VERSION + 1}")
        with pytest.raises(UnsupportedSchemaVersionError):
            initialize_schema(connection)
        assert int(connection.execute("PRAGMA user_version").fetchone()[0]) == SCHEMA_VERSION + 1
    finally:
        connection.close()
