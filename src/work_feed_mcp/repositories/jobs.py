"""Detailed job query repository for MCP and agent consumers."""

from __future__ import annotations

import sqlite3
from typing import Any


def recent_jobs(connection: sqlite3.Connection, *, limit: int = 20) -> list[dict[str, Any]]:
    rows = connection.execute(
        _base_sql() + " ORDER BY jobs.first_seen_at DESC, jobs.job_id ASC LIMIT ?",
        (limit,),
    ).fetchall()
    return [_job_row(connection, row) for row in rows]


def search_jobs(
    connection: sqlite3.Connection,
    *,
    title: str | None = None,
    skill: str | None = None,
    limit: int = 20,
) -> list[dict[str, Any]]:
    where: list[str] = []
    params: list[Any] = []
    if title:
        where.append("LOWER(jobs.title) LIKE ?")
        params.append(f"%{title.casefold()}%")
    if skill:
        where.append(
            """
            EXISTS (
              SELECT 1 FROM job_skills js
               WHERE js.job_id = jobs.job_id AND js.skill = ?
            )
            """
        )
        params.append(" ".join(skill.strip().split()).casefold())
    sql = _base_sql()
    if where:
        sql += " WHERE " + " AND ".join(f"({clause})" for clause in where)
    sql += " ORDER BY jobs.first_seen_at DESC, jobs.job_id ASC LIMIT ?"
    params.append(limit)
    rows = connection.execute(sql, params).fetchall()
    return [_job_row(connection, row) for row in rows]


def get_job(connection: sqlite3.Connection, job_id: str) -> dict[str, Any] | None:
    row = connection.execute(_base_sql() + " WHERE jobs.job_id = ?", (job_id,)).fetchone()
    return _job_row(connection, row) if row is not None else None


def _base_sql() -> str:
    return """
        SELECT job_id, source, title, description, url, posted_at, job_type,
               contractor_tier, hourly_min, hourly_max, fixed_amount, raw_id,
               content_hash, first_seen_at, created_at
          FROM jobs
    """


def _skills(connection: sqlite3.Connection, job_id: str) -> list[str]:
    rows = connection.execute(
        "SELECT skill FROM job_skills WHERE job_id = ? ORDER BY skill ASC", (job_id,)
    ).fetchall()
    return [str(row["skill"]) for row in rows]


def _job_row(connection: sqlite3.Connection, row: sqlite3.Row) -> dict[str, Any]:
    job_id = str(row["job_id"])
    return {
        "job_id": job_id,
        "source": str(row["source"]),
        "title": str(row["title"]),
        "description": row["description"],
        "url": row["url"],
        "skills": _skills(connection, job_id),
        "posted_at": row["posted_at"],
        "job_type": row["job_type"],
        "contractor_tier": row["contractor_tier"],
        "hourly_min": row["hourly_min"],
        "hourly_max": row["hourly_max"],
        "fixed_amount": row["fixed_amount"],
        "raw_id": row["raw_id"],
        "content_hash": str(row["content_hash"]),
        "first_seen_at": str(row["first_seen_at"]),
        "created_at": str(row["created_at"]),
    }
