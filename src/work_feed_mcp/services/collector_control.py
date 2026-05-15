"""Collector control/config service helpers."""

from __future__ import annotations

import sqlite3
from dataclasses import dataclass
from pathlib import Path
from typing import Any, Literal

from work_feed_mcp.db.connection import connect_control, connect_readonly, schema_has_tables
from work_feed_mcp.repositories import collector_control

CONTROL_TABLES = {"collector_config", "collector_commands"}
BASE_TABLES = {"jobs", "job_skills", "collector_runs", "collector_run_results"}

NotReadyReason = Literal["db_missing", "schema_missing"]


@dataclass(frozen=True, slots=True)
class NotReadyError(Exception):
    reason: NotReadyReason

    def to_dict(self) -> dict[str, Any]:
        return {
            "ok": False,
            "error": "not_ready",
            "reason": self.reason,
            "next_action": "start work-feed-worker",
        }


def not_ready_payload(reason: NotReadyReason) -> dict[str, Any]:
    return NotReadyError(reason).to_dict()


def ensure_ready_read(db_path: str) -> sqlite3.Connection:
    if not Path(db_path).exists():
        raise NotReadyError("db_missing")
    connection = connect_readonly(db_path)
    if not schema_has_tables(connection, BASE_TABLES | CONTROL_TABLES):
        connection.close()
        raise NotReadyError("schema_missing")
    return connection


def ensure_ready_control(db_path: str) -> sqlite3.Connection:
    if not Path(db_path).exists():
        raise NotReadyError("db_missing")
    connection = connect_control(db_path)
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
