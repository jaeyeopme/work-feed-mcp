"""SQLite connection helpers."""

from __future__ import annotations

import sqlite3
from pathlib import Path
from types import TracebackType
from typing import Literal

from work_feed_mcp.db.schema import initialize_schema

BUSY_TIMEOUT_MS = 10_000


class ClosingConnection(sqlite3.Connection):
    """SQLite connection whose context manager also closes the handle."""

    def __exit__(
        self,
        exc_type: type[BaseException] | None,
        exc_value: BaseException | None,
        traceback: TracebackType | None,
    ) -> Literal[False]:
        try:
            super().__exit__(exc_type, exc_value, traceback)
        finally:
            self.close()
        return False


def _sqlite_uri(db_path: str, *, mode: str) -> str:
    return f"file:{Path(db_path)}?mode={mode}"


def _prepare_parent(db_path: str) -> None:
    parent = Path(db_path).parent
    if parent != Path(""):
        parent.mkdir(parents=True, exist_ok=True)


def _base_connection(db_path: str, *, mode: str) -> sqlite3.Connection:
    connection = sqlite3.connect(
        _sqlite_uri(db_path, mode=mode),
        uri=True,
        factory=ClosingConnection,
    )
    connection.row_factory = sqlite3.Row
    connection.execute(f"PRAGMA busy_timeout = {BUSY_TIMEOUT_MS}")
    return connection


def connect_readonly(db_path: str) -> sqlite3.Connection:
    """Open an existing database read-only without initializing schema."""

    return _base_connection(db_path, mode="ro")


def connect_worker(db_path: str) -> sqlite3.Connection:
    """Open/create the worker-owned write database and initialize schema/pragmas."""

    _prepare_parent(db_path)
    connection = _base_connection(db_path, mode="rwc")
    connection.execute("PRAGMA journal_mode = WAL")
    connection.execute("PRAGMA foreign_keys = ON")
    connection.execute("PRAGMA synchronous = NORMAL")
    initialize_schema(connection)
    return connection


def connect_control(db_path: str) -> sqlite3.Connection:
    """Open an existing database for MCP control writes without initializing schema."""

    connection = _base_connection(db_path, mode="rw")
    connection.execute("PRAGMA foreign_keys = ON")
    return connection


def schema_has_tables(connection: sqlite3.Connection, tables: set[str]) -> bool:
    if not tables:
        return True
    placeholders = ",".join("?" for _ in tables)
    rows = connection.execute(
        f"SELECT name FROM sqlite_master WHERE type = 'table' AND name IN ({placeholders})",
        tuple(tables),
    ).fetchall()
    return {str(row["name"]) for row in rows} == tables
