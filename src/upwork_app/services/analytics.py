"""Analytics service layer over SQLite repositories."""

from __future__ import annotations

import sqlite3
from dataclasses import dataclass

from upwork_app.db.connection import connect_readonly
from upwork_app.repositories import analytics

QueryResult = analytics.QueryResult


@dataclass(slots=True)
class AnalyticsServiceError(Exception):
    message: str
    status_code: int = 503

    def __str__(self) -> str:
        return self.message


def query_database(
    db_path: str,
    name: str,
    *,
    skill: str | None = None,
    title: str | None = None,
) -> QueryResult:
    try:
        connection = connect_readonly(db_path)
        try:
            return run_query(connection, name, skill=skill, title=title)
        finally:
            connection.close()
    except sqlite3.OperationalError as exc:
        raise AnalyticsServiceError("analytics database unavailable", status_code=503) from exc
    except sqlite3.Error as exc:
        raise AnalyticsServiceError("analytics query failed", status_code=500) from exc


def run_query(
    connection: sqlite3.Connection,
    name: str,
    *,
    skill: str | None = None,
    title: str | None = None,
) -> QueryResult:
    match name:
        case "summary":
            return analytics.summary(connection)
        case "skills":
            return analytics.skills(connection)
        case "jobs":
            return analytics.jobs(connection, skill=skill, title=title)
        case "budgets":
            return analytics.budgets(connection)
        case "clients":
            return analytics.clients(connection)
    raise ValueError(f"unknown analytics query: {name}")
