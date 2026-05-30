"""Agent-readable scheduler status over SQLite run history."""

from __future__ import annotations

import sqlite3
from dataclasses import dataclass
from typing import Any

from work_feed_mcp.repositories import run_history
from work_feed_mcp.services.collector_control import NotReadyError, ensure_ready_read


@dataclass(slots=True)
class SchedulerStatusError(Exception):
    message: str

    def __str__(self) -> str:
        return self.message


def scheduler_status(db_path: str, *, limit: int = 5) -> dict[str, Any]:
    try:
        connection = ensure_ready_read(db_path)
    except NotReadyError as exc:
        return exc.to_dict()
    try:
        try:
            last_run = run_history.latest_run(connection)
            run_id = str(last_run["run_id"]) if last_run else None
            return {
                "ok": True,
                "query": "scheduler-status",
                "db_path": db_path,
                "last_run": last_run,
                "recent_runs": run_history.recent_runs(connection, limit=limit),
                "recent_results": run_history.recent_results(
                    connection,
                    run_id=run_id,
                    limit=limit,
                )
                if run_id
                else [],
            }
        finally:
            connection.close()
    except sqlite3.OperationalError as exc:
        raise SchedulerStatusError("scheduler status database unavailable") from exc
    except sqlite3.Error as exc:
        raise SchedulerStatusError("scheduler status query failed") from exc
