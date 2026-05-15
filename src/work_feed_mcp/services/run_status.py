"""Pure read-only run/status service for MCP and agent consumers."""

from __future__ import annotations

from typing import Any

from work_feed_mcp.repositories import collector_control, run_history
from work_feed_mcp.services.collector_control import ensure_ready_read


def run_status(db_path: str, *, limit: int = 5) -> dict[str, Any]:
    connection = ensure_ready_read(db_path)
    try:
        last_run = run_history.latest_run(connection)
        recent_runs = run_history.recent_runs(connection, limit=limit)
        recent_commands = collector_control.recent_commands(connection, limit=limit)
        config = collector_control.get_config(connection)
        run_id = str(last_run["run_id"]) if last_run else None
        recent_results = (
            run_history.recent_results(connection, run_id=run_id, limit=limit) if run_id else []
        )
        return {
            "ok": True,
            "status": "empty" if last_run is None else str(last_run["status"]),
            "last_run": last_run,
            "recent_runs": recent_runs,
            "recent_results": recent_results,
            "recent_commands": recent_commands,
            "config": config,
        }
    finally:
        connection.close()
