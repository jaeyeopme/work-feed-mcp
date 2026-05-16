"""SQLite repository for collector runtime config and command queue."""

from __future__ import annotations

import json
import sqlite3
import uuid
from typing import Any

from work_feed_mcp.core.time import utc_now

CONFIG_KEYS = {"interval_seconds", "queries", "max_pages", "page_size", "paused"}
COMMAND_TYPES = {"run_once", "pause", "resume", "update_config"}
TERMINAL_STATUSES = {"applied", "failed"}


def seed_config(connection: sqlite3.Connection, defaults: dict[str, Any]) -> None:
    now = utc_now()
    for key, value in defaults.items():
        if key not in CONFIG_KEYS:
            continue
        connection.execute(
            """
            INSERT OR IGNORE INTO collector_config (key, value_json, updated_at, updated_by)
            VALUES (?, ?, ?, 'worker')
            """,
            (key, json.dumps(value), now),
        )


def get_config(connection: sqlite3.Connection) -> dict[str, Any]:
    rows = connection.execute(
        "SELECT key, value_json FROM collector_config ORDER BY key ASC"
    ).fetchall()
    return {str(row["key"]): json.loads(str(row["value_json"])) for row in rows}


def update_config(
    connection: sqlite3.Connection, updates: dict[str, Any], *, updated_by: str = "mcp"
) -> dict[str, Any]:
    validate_config_updates(updates)
    now = utc_now()
    for key, value in updates.items():
        connection.execute(
            """
            INSERT INTO collector_config (key, value_json, updated_at, updated_by)
            VALUES (?, ?, ?, ?)
            ON CONFLICT(key) DO UPDATE SET
              value_json = excluded.value_json,
              updated_at = excluded.updated_at,
              updated_by = excluded.updated_by
            """,
            (key, json.dumps(value), now, updated_by),
        )
    return get_config(connection)


def validate_config_updates(updates: dict[str, Any]) -> None:
    invalid = sorted(set(updates) - CONFIG_KEYS)
    if invalid:
        raise ValueError(f"unsupported config keys: {', '.join(invalid)}")
    for key, value in updates.items():
        if key in {"interval_seconds", "max_pages", "page_size"}:
            if not isinstance(value, int) or isinstance(value, bool) or value < 1:
                raise ValueError(f"{key} must be a positive integer")
        elif key == "paused":
            if not isinstance(value, bool):
                raise ValueError("paused must be a boolean")
        elif key == "queries" and (
            not isinstance(value, list)
            or not all(isinstance(item, str) and item.strip() for item in value)
        ):
            raise ValueError("queries must be a list of non-empty strings")


def enqueue_command(
    connection: sqlite3.Connection,
    command_type: str,
    *,
    payload: dict[str, Any] | None = None,
    requested_by: str = "mcp",
    command_id: str | None = None,
) -> dict[str, Any]:
    if command_type not in COMMAND_TYPES:
        raise ValueError(f"unsupported command type: {command_type}")
    resolved_id = command_id or uuid.uuid4().hex
    now = utc_now()
    connection.execute(
        """
        INSERT INTO collector_commands (
          command_id, command_type, payload_json, status, created_at, requested_by
        ) VALUES (?, ?, ?, 'queued', ?, ?)
        """,
        (resolved_id, command_type, json.dumps(payload or {}), now, requested_by),
    )
    return {"ok": True, "command_id": resolved_id, "status": "queued"}


def next_queued_command(connection: sqlite3.Connection) -> dict[str, Any] | None:
    row = connection.execute(
        """
        SELECT command_id, command_type, payload_json, status, created_at, started_at,
               finished_at, requested_by, result_json, error_type, redacted_error
          FROM collector_commands
         WHERE status = 'queued'
         ORDER BY created_at ASC, command_id ASC
         LIMIT 1
        """
    ).fetchone()
    return _command_row(row) if row is not None else None


def mark_running(connection: sqlite3.Connection, command_id: str) -> None:
    connection.execute(
        "UPDATE collector_commands SET status = 'running', started_at = ? WHERE command_id = ?",
        (utc_now(), command_id),
    )


def mark_applied(
    connection: sqlite3.Connection, command_id: str, *, result: dict[str, Any] | None = None
) -> None:
    connection.execute(
        """
        UPDATE collector_commands
           SET status = 'applied', finished_at = ?, result_json = ?
         WHERE command_id = ?
        """,
        (utc_now(), json.dumps(result or {}), command_id),
    )


def mark_failed(
    connection: sqlite3.Connection,
    command_id: str,
    *,
    error_type: str,
    redacted_error: str,
) -> None:
    connection.execute(
        """
        UPDATE collector_commands
           SET status = 'failed', finished_at = ?, error_type = ?, redacted_error = ?
         WHERE command_id = ?
        """,
        (utc_now(), error_type, redacted_error, command_id),
    )


def command_status(connection: sqlite3.Connection, command_id: str) -> dict[str, Any] | None:
    row = connection.execute(
        """
        SELECT command_id, command_type, payload_json, status, created_at, started_at,
               finished_at, requested_by, result_json, error_type, redacted_error
          FROM collector_commands
         WHERE command_id = ?
        """,
        (command_id,),
    ).fetchone()
    return _command_row(row) if row is not None else None


def recent_commands(connection: sqlite3.Connection, *, limit: int = 5) -> list[dict[str, Any]]:
    rows = connection.execute(
        """
        SELECT command_id, command_type, payload_json, status, created_at, started_at,
               finished_at, requested_by, result_json, error_type, redacted_error
          FROM collector_commands
         ORDER BY created_at DESC, command_id DESC
         LIMIT ?
        """,
        (limit,),
    ).fetchall()
    return [_command_row(row) for row in rows]


def _command_row(row: sqlite3.Row) -> dict[str, Any]:
    result_json = row["result_json"]
    return {
        "command_id": str(row["command_id"]),
        "command_type": str(row["command_type"]),
        "payload": json.loads(str(row["payload_json"])),
        "status": str(row["status"]),
        "created_at": str(row["created_at"]),
        "started_at": row["started_at"],
        "finished_at": row["finished_at"],
        "requested_by": str(row["requested_by"]),
        "result": json.loads(str(result_json)) if result_json is not None else None,
        "error_type": row["error_type"],
        "redacted_error": row["redacted_error"],
    }
