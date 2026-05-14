"""SQLite helpers for collector run history and status."""

from __future__ import annotations

import sqlite3
from dataclasses import dataclass
from typing import Any


@dataclass(frozen=True, slots=True)
class RunTotals:
    seen: int = 0
    inserted: int = 0
    skipped: int = 0

    def add(self, *, seen: int, inserted: int, skipped: int) -> RunTotals:
        return RunTotals(
            seen=self.seen + seen,
            inserted=self.inserted + inserted,
            skipped=self.skipped + skipped,
        )


def create_run(
    connection: sqlite3.Connection,
    *,
    run_id: str,
    started_at: str,
    trigger: str,
    query_count: int,
) -> None:
    connection.execute(
        """
        INSERT INTO collector_runs (
          run_id, started_at, status, trigger, query_count, created_at
        ) VALUES (?, ?, 'running', ?, ?, ?)
        """,
        (run_id, started_at, trigger, query_count, started_at),
    )


def finish_run_success(
    connection: sqlite3.Connection,
    *,
    run_id: str,
    finished_at: str,
    totals: RunTotals,
) -> None:
    _finish_run(
        connection,
        run_id=run_id,
        finished_at=finished_at,
        status="success",
        totals=totals,
        error_type=None,
        redacted_error=None,
    )


def finish_run_failure(
    connection: sqlite3.Connection,
    *,
    run_id: str,
    finished_at: str,
    totals: RunTotals,
    error_type: str,
    redacted_error: str,
) -> None:
    _finish_run(
        connection,
        run_id=run_id,
        finished_at=finished_at,
        status="failed",
        totals=totals,
        error_type=error_type,
        redacted_error=redacted_error,
    )


def _finish_run(
    connection: sqlite3.Connection,
    *,
    run_id: str,
    finished_at: str,
    status: str,
    totals: RunTotals,
    error_type: str | None,
    redacted_error: str | None,
) -> None:
    connection.execute(
        """
        UPDATE collector_runs
           SET finished_at = ?,
               status = ?,
               total_seen = ?,
               total_inserted = ?,
               total_skipped = ?,
               error_type = ?,
               redacted_error = ?
         WHERE run_id = ?
        """,
        (
            finished_at,
            status,
            totals.seen,
            totals.inserted,
            totals.skipped,
            error_type,
            redacted_error,
            run_id,
        ),
    )


def insert_run_result(
    connection: sqlite3.Connection,
    *,
    run_id: str,
    query: str | None,
    status: str,
    attempts: int,
    seen_count: int,
    inserted_count: int,
    skipped_count: int,
    error_type: str | None,
    redacted_error: str | None,
    started_at: str,
    finished_at: str,
) -> None:
    connection.execute(
        """
        INSERT INTO collector_run_results (
          run_id, query, status, attempts, seen_count, inserted_count, skipped_count,
          error_type, redacted_error, started_at, finished_at
        ) VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
        """,
        (
            run_id,
            query,
            status,
            attempts,
            seen_count,
            inserted_count,
            skipped_count,
            error_type,
            redacted_error,
            started_at,
            finished_at,
        ),
    )


def latest_run(connection: sqlite3.Connection) -> dict[str, Any] | None:
    row = connection.execute(
        """
        SELECT run_id, started_at, finished_at, status, trigger, query_count,
               total_seen, total_inserted, total_skipped, error_type, redacted_error
          FROM collector_runs
         ORDER BY started_at DESC, run_id DESC
         LIMIT 1
        """
    ).fetchone()
    return _run_row(row) if row is not None else None


def recent_runs(connection: sqlite3.Connection, *, limit: int) -> list[dict[str, Any]]:
    rows = connection.execute(
        """
        SELECT run_id, started_at, finished_at, status, trigger, query_count,
               total_seen, total_inserted, total_skipped, error_type, redacted_error
          FROM collector_runs
         ORDER BY started_at DESC, run_id DESC
         LIMIT ?
        """,
        (limit,),
    ).fetchall()
    return [_run_row(row) for row in rows]


def recent_results(
    connection: sqlite3.Connection, *, run_id: str | None = None, limit: int
) -> list[dict[str, Any]]:
    params: tuple[Any, ...]
    where = ""
    if run_id is None:
        params = (limit,)
    else:
        where = "WHERE run_id = ?"
        params = (run_id, limit)
    rows = connection.execute(
        f"""
        SELECT id, run_id, query, status, attempts, seen_count, inserted_count,
               skipped_count, error_type, redacted_error, started_at, finished_at
          FROM collector_run_results
          {where}
         ORDER BY started_at DESC, id DESC
         LIMIT ?
        """,
        params,
    ).fetchall()
    return [_result_row(row) for row in rows]


def _duration_seconds(started_at: str, finished_at: str | None) -> int | None:
    if finished_at is None:
        return None
    from datetime import datetime

    try:
        started = datetime.fromisoformat(started_at.replace("Z", "+00:00"))
        finished = datetime.fromisoformat(finished_at.replace("Z", "+00:00"))
    except ValueError:
        return None
    return int((finished - started).total_seconds())


def _run_row(row: sqlite3.Row) -> dict[str, Any]:
    started_at = str(row["started_at"])
    finished = row["finished_at"]
    finished_at = str(finished) if finished is not None else None
    return {
        "run_id": str(row["run_id"]),
        "started_at": started_at,
        "finished_at": finished_at,
        "duration_seconds": _duration_seconds(started_at, finished_at),
        "status": str(row["status"]),
        "trigger": str(row["trigger"]),
        "query_count": int(row["query_count"]),
        "total_seen": int(row["total_seen"]),
        "total_inserted": int(row["total_inserted"]),
        "total_skipped": int(row["total_skipped"]),
        "error_type": row["error_type"],
        "redacted_error": row["redacted_error"],
    }


def _result_row(row: sqlite3.Row) -> dict[str, Any]:
    return {
        "id": int(row["id"]),
        "run_id": str(row["run_id"]),
        "query": row["query"],
        "status": str(row["status"]),
        "attempts": int(row["attempts"]),
        "seen_count": int(row["seen_count"]),
        "inserted_count": int(row["inserted_count"]),
        "skipped_count": int(row["skipped_count"]),
        "error_type": row["error_type"],
        "redacted_error": row["redacted_error"],
        "started_at": str(row["started_at"]),
        "finished_at": str(row["finished_at"]),
    }
