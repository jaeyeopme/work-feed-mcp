"""MCP-safe job query service."""

from __future__ import annotations

from typing import Any

from work_feed_mcp.repositories import jobs
from work_feed_mcp.services.collector_control import NotReadyError, ensure_ready_read


def jobs_recent(db_path: str, *, limit: int = 20) -> dict[str, Any]:
    connection = ensure_ready_read(db_path)
    try:
        rows = jobs.recent_jobs(connection, limit=limit)
        return {"ok": True, "status": "empty" if not rows else "ok", "rows": rows}
    finally:
        connection.close()


def jobs_search(
    db_path: str, *, title: str | None = None, skill: str | None = None, limit: int = 20
) -> dict[str, Any]:
    connection = ensure_ready_read(db_path)
    try:
        rows = jobs.search_jobs(connection, title=title, skill=skill, limit=limit)
        return {"ok": True, "status": "empty" if not rows else "ok", "rows": rows}
    finally:
        connection.close()


def jobs_get(db_path: str, *, job_id: str) -> dict[str, Any]:
    connection = ensure_ready_read(db_path)
    try:
        job = jobs.get_job(connection, job_id)
        if job is None:
            return {"ok": False, "error": "not_found", "job_id": job_id}
        return {"ok": True, "job": job}
    finally:
        connection.close()


__all__ = ["NotReadyError", "jobs_recent", "jobs_search", "jobs_get"]
