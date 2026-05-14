from __future__ import annotations

import sqlite3

from upwork_app.repositories import run_history
from upwork_app.repositories.run_history import RunTotals


def insert_success_run(
    connection: sqlite3.Connection,
    *,
    run_id: str = "run-1",
    started_at: str = "2026-05-14T00:00:00Z",
    finished_at: str = "2026-05-14T00:00:05Z",
    query: str | None = None,
    seen: int = 50,
    inserted: int = 10,
    skipped: int = 40,
) -> None:
    run_history.create_run(
        connection,
        run_id=run_id,
        started_at=started_at,
        trigger="scheduled",
        query_count=1,
    )
    run_history.insert_run_result(
        connection,
        run_id=run_id,
        query=query,
        status="success",
        attempts=1,
        seen_count=seen,
        inserted_count=inserted,
        skipped_count=skipped,
        error_type=None,
        redacted_error=None,
        started_at=started_at,
        finished_at=finished_at,
    )
    run_history.finish_run_success(
        connection,
        run_id=run_id,
        finished_at=finished_at,
        totals=RunTotals(seen=seen, inserted=inserted, skipped=skipped),
    )
