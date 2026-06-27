"""Analytics service layer over SQLite repositories."""

from __future__ import annotations

import sqlite3
from dataclasses import dataclass

from work_feed_mcp.db.connection import connect_readonly
from work_feed_mcp.repositories import analytics
from work_feed_mcp.services.limits import MAX_QUERY_LIMIT, validate_limit

QueryResult = analytics.QueryResult


@dataclass(slots=True)
class AnalyticsServiceError(Exception):
    message: str

    def __str__(self) -> str:
        return self.message


def query_database(
    db_path: str,
    name: str,
    *,
    skill: str | None = None,
    title: str | None = None,
    limit: int | None = None,
) -> QueryResult:
    try:
        connection = connect_readonly(db_path)
        try:
            return run_query(connection, name, skill=skill, title=title, limit=limit)
        finally:
            connection.close()
    except sqlite3.OperationalError as exc:
        raise AnalyticsServiceError("analytics database unavailable") from exc
    except sqlite3.Error as exc:
        raise AnalyticsServiceError("analytics query failed") from exc


def run_query(
    connection: sqlite3.Connection,
    name: str,
    *,
    skill: str | None = None,
    title: str | None = None,
    limit: int | None = None,
) -> QueryResult:
    match name:
        case "summary":
            return analytics.summary(connection)
        case "skills":
            return analytics.skills(connection)
        case "jobs":
            resolved_limit = validate_limit(MAX_QUERY_LIMIT if limit is None else limit)
            return analytics.jobs(connection, skill=skill, title=title, limit=resolved_limit)
        case "budgets":
            return analytics.budgets(connection)
    raise ValueError(f"unknown analytics query: {name}")
