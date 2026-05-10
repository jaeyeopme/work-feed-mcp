"""SQLite-backed analytics queries for persisted Upwork jobs."""

from __future__ import annotations

import sqlite3
from collections.abc import Iterable
from dataclasses import asdict, dataclass
from typing import Any

from upwork_app.repositories.client_analytics import client_dimension_buckets


@dataclass(frozen=True, slots=True)
class QueryResult:
    """JSON-serializable analytics query result."""

    query: str
    rows: tuple[dict[str, Any], ...]

    def to_dict(self) -> dict[str, Any]:
        return {"query": self.query, "rows": list(self.rows)}


def summary(connection: sqlite3.Connection) -> QueryResult:
    """Return high-level job/run/raw-record counts."""

    rows = [
        {
            "jobs": _count_table(connection, "jobs"),
            "runs": _count_table(connection, "ingest_runs"),
            "observations": _count_table(connection, "job_observations"),
            "raw_records": _count_table(connection, "raw_records"),
        }
    ]
    return QueryResult(query="summary", rows=tuple(rows))


def skills(connection: sqlite3.Connection) -> QueryResult:
    """Return top skills by normalized frequency."""

    rows = _dict_rows(
        connection.execute(
            """
            SELECT skill, COUNT(*) AS count
              FROM job_skills
             GROUP BY skill
             ORDER BY count DESC, skill ASC
            """
        )
    )
    return QueryResult(query="skills", rows=tuple(rows))


def jobs(
    connection: sqlite3.Connection,
    *,
    skill: str | None = None,
    title: str | None = None,
) -> QueryResult:
    """Return jobs optionally filtered by skill and/or title keyword."""

    where: list[str] = []
    params: list[Any] = []
    if skill:
        where.append(
            """
            EXISTS (
              SELECT 1 FROM job_skills js
               WHERE js.job_id = jobs.job_id
                 AND js.skill = ?
            )
            """
        )
        params.append(_normalize_skill(skill))
    if title:
        where.append("LOWER(jobs.title) LIKE ?")
        params.append(f"%{title.casefold()}%")

    sql = """
        SELECT job_id, title, url, job_type, hourly_min, hourly_max, fixed_amount,
               first_seen_at, last_seen_at
          FROM jobs
    """
    if where:
        sql += " WHERE " + " AND ".join(f"({clause})" for clause in where)
    sql += " ORDER BY last_seen_at DESC, job_id ASC"
    return QueryResult(query="jobs", rows=tuple(_dict_rows(connection.execute(sql, params))))


def budgets(connection: sqlite3.Connection) -> QueryResult:
    """Return budget/rate distribution without fabricating missing values."""

    rows = _dict_rows(
        connection.execute(
            """
            SELECT
              CASE
                WHEN fixed_amount IS NOT NULL THEN 'fixed'
                WHEN hourly_min IS NOT NULL OR hourly_max IS NOT NULL THEN 'hourly'
                ELSE 'unknown'
              END AS budget_type,
              COUNT(*) AS count,
              MIN(hourly_min) AS min_hourly_min,
              MAX(hourly_max) AS max_hourly_max,
              MIN(fixed_amount) AS min_fixed_amount,
              MAX(fixed_amount) AS max_fixed_amount
            FROM jobs
            GROUP BY budget_type
            ORDER BY budget_type
            """
        )
    )
    return QueryResult(query="budgets", rows=tuple(rows))


def runs(connection: sqlite3.Connection) -> QueryResult:
    """Return ingest run stats."""

    rows = _dict_rows(
        connection.execute(
            """
            SELECT run_id, source_query, input_path, started_at, completed_at, record_count, status
              FROM ingest_runs
             ORDER BY started_at DESC, run_id ASC
            """
        )
    )
    return QueryResult(query="runs", rows=tuple(rows))


def clients(connection: sqlite3.Connection) -> QueryResult:
    """Return conditional client-dimension buckets."""

    rows: list[dict[str, Any]] = []
    for dimension in client_dimension_buckets(connection):
        for bucket in dimension.buckets:
            rows.append(
                {
                    "dimension": dimension.name,
                    "available": dimension.available,
                    **asdict(bucket),
                }
            )
    return QueryResult(query="clients", rows=tuple(rows))


def _count_table(connection: sqlite3.Connection, table: str) -> int:
    if table not in _table_names(connection):
        return 0
    row = connection.execute(f'SELECT COUNT(*) FROM "{table}"').fetchone()
    return int(row[0]) if row else 0


def _table_names(connection: sqlite3.Connection) -> set[str]:
    return {
        str(row[0])
        for row in connection.execute("SELECT name FROM sqlite_master WHERE type = 'table'")
    }


def _dict_rows(cursor: Iterable[sqlite3.Row] | sqlite3.Cursor) -> list[dict[str, Any]]:
    return [dict(row) for row in cursor]


def _normalize_skill(value: str) -> str:
    return " ".join(value.strip().split()).casefold()
