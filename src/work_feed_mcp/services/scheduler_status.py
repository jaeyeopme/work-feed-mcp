"""Agent-readable scheduler status over SQLite run history."""

from __future__ import annotations

import sqlite3
from dataclasses import dataclass
from typing import Any

from work_feed_mcp.db.schema import initialize_schema
from work_feed_mcp.repositories import run_history


@dataclass(slots=True)
class SchedulerStatusError(Exception):
    message: str

    def __str__(self) -> str:
        return self.message


def scheduler_status(db_path: str, *, limit: int = 5) -> dict[str, Any]:
    try:
        connection = sqlite3.connect(db_path)
        connection.row_factory = sqlite3.Row
        try:
            initialize_schema(connection)
            connection.commit()
            last_run = run_history.latest_run(connection)
            run_id = str(last_run["run_id"]) if last_run else None
            return {
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
