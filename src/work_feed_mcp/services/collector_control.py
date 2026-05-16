"""Collector control/config service helpers."""

from __future__ import annotations

import sqlite3
from collections.abc import Callable
from dataclasses import dataclass
from pathlib import Path
from typing import Any, Literal

from work_feed_mcp.db.connection import connect_control, connect_readonly, schema_has_tables
from work_feed_mcp.db.schema import UnsupportedSchemaVersionError, assert_supported_schema_version
from work_feed_mcp.repositories import collector_control

CONTROL_TABLES = {"collector_config", "collector_commands"}
BASE_TABLES = {"jobs", "job_skills", "collector_runs", "collector_run_results"}

NotReadyReason = Literal["db_missing", "schema_missing", "unsupported_schema"]


@dataclass(frozen=True, slots=True)
class NotReadyError(Exception):
    reason: NotReadyReason

    def to_dict(self) -> dict[str, Any]:
        next_action = (
            "upgrade work-feed or migrate the database"
            if self.reason == "unsupported_schema"
            else "start work-feed-worker"
        )
        return {
            "ok": False,
            "error": "not_ready",
            "reason": self.reason,
            "next_action": next_action,
        }


def not_ready_payload(reason: NotReadyReason) -> dict[str, Any]:
    return NotReadyError(reason).to_dict()


def ensure_ready_read(db_path: str) -> sqlite3.Connection:
    return _ensure_mcp_runtime_ready(db_path, connect_readonly)


def ensure_ready_control(db_path: str) -> sqlite3.Connection:
    return _ensure_mcp_runtime_ready(db_path, connect_control)


def _ensure_mcp_runtime_ready(
    db_path: str, connect: Callable[[str], sqlite3.Connection]
) -> sqlite3.Connection:
    """Open an existing worker-initialized runtime DB for MCP read/control paths."""
    if not Path(db_path).exists():
        raise NotReadyError("db_missing")
    connection = connect(db_path)
    try:
        assert_supported_schema_version(connection)
    except UnsupportedSchemaVersionError as exc:
        connection.close()
        raise NotReadyError("unsupported_schema") from exc
    if not schema_has_tables(connection, BASE_TABLES | CONTROL_TABLES):
        connection.close()
        raise NotReadyError("schema_missing")
    return connection


def get_effective_config(db_path: str) -> dict[str, Any]:
    connection = ensure_ready_read(db_path)
    try:
        return {"ok": True, "config": collector_control.get_config(connection)}
    finally:
        connection.close()


def update_runtime_config(db_path: str, updates: dict[str, Any]) -> dict[str, Any]:
    collector_control.validate_config_updates(updates)
    connection = ensure_ready_control(db_path)
    try:
        result = collector_control.enqueue_command(
            connection, "update_config", payload={"updates": updates}
        )
        connection.commit()
        return result
    finally:
        connection.close()


def enqueue_runtime_command(
    db_path: str, command_type: str, payload: dict[str, Any] | None = None
) -> dict[str, Any]:
    connection = ensure_ready_control(db_path)
    try:
        result = collector_control.enqueue_command(connection, command_type, payload=payload)
        connection.commit()
        return result
    finally:
        connection.close()


def get_command_status(db_path: str, command_id: str) -> dict[str, Any]:
    connection = ensure_ready_read(db_path)
    try:
        command = collector_control.command_status(connection, command_id)
        if command is None:
            return {"ok": False, "error": "not_found", "command_id": command_id}
        return {"ok": True, "command": command}
    finally:
        connection.close()
