"""One-shot collection orchestration for the worker and debug CLIs."""

from __future__ import annotations

import sqlite3
import uuid
from collections.abc import Callable
from dataclasses import asdict, dataclass
from typing import Any

from work_feed_mcp.core.time import utc_now
from work_feed_mcp.db.connection import connect_worker
from work_feed_mcp.domain.collector_record import CollectorRecord, validate_payload
from work_feed_mcp.integrations.upwork.credentials import redact
from work_feed_mcp.integrations.upwork.errors import CollectorError
from work_feed_mcp.integrations.upwork.models import Job
from work_feed_mcp.repositories import run_history
from work_feed_mcp.repositories.run_history import RunTotals
from work_feed_mcp.services.collector import collect_jobs
from work_feed_mcp.services.ingestion import ingest_records_into_connection
from work_feed_mcp.services.retry import Jitter, RetryExhausted, Sleep, collect_with_retry

QueryValue = str | None


@dataclass(frozen=True, slots=True)
class ScheduledQueryResult:
    query: str | None
    seen_count: int
    inserted_count: int
    skipped_count: int
    attempts: int = 1

    def to_dict(self) -> dict[str, Any]:
        return asdict(self)


@dataclass(frozen=True, slots=True)
class ScheduledCollectionResult:
    db_path: str
    query_count: int
    results: tuple[ScheduledQueryResult, ...]
    run_id: str | None = None

    def to_dict(self) -> dict[str, Any]:
        return {
            "db_path": self.db_path,
            "query_count": self.query_count,
            "run_id": self.run_id,
            "results": [result.to_dict() for result in self.results],
        }


def parse_queries(value: str) -> tuple[str, ...]:
    """Parse comma-separated query option text."""

    queries = tuple(part.strip() for part in value.split(",") if part.strip())
    if not queries:
        raise ValueError("--queries must contain at least one query")
    return queries


def default_queries(queries: tuple[str, ...] | None) -> tuple[QueryValue, ...]:
    if queries is None:
        return (None,)
    return queries


def _records_from_jobs(jobs: list[Job]) -> list[CollectorRecord]:
    return [validate_payload(job.to_dict()) for job in jobs]


def _connect_for_write(db_path: str) -> sqlite3.Connection:
    return connect_worker(db_path)


def _error_type(error: BaseException) -> str:
    return type(error).__name__


def _record_failed_query(
    connection: sqlite3.Connection,
    *,
    run_id: str,
    query: QueryValue,
    attempts: int,
    totals: RunTotals,
    error: BaseException,
    started_at: str,
    finished_at: str,
) -> None:
    redacted = redact(error)
    error_type = _error_type(error)
    run_history.insert_run_result(
        connection,
        run_id=run_id,
        query=query,
        status="failed",
        attempts=attempts,
        seen_count=0,
        inserted_count=0,
        skipped_count=0,
        error_type=error_type,
        redacted_error=redacted,
        started_at=started_at,
        finished_at=finished_at,
    )
    run_history.finish_run_failure(
        connection,
        run_id=run_id,
        finished_at=finished_at,
        totals=totals,
        error_type=error_type,
        redacted_error=redacted,
    )


def collect_scheduled(
    *,
    db_path: str,
    queries: tuple[str, ...] | None = None,
    max_pages: int = 1,
    page_size: int = 50,
    sleep: Sleep | None = None,
    jitter: Jitter | None = None,
    run_id_factory: Callable[[], str] | None = None,
    trigger: str = "scheduled",
    live: bool = True,
    fixture: str | None = None,
) -> ScheduledCollectionResult:
    """Collect and ingest live queries sequentially with operational run history.

    This is intentionally one-shot: the Docker worker owns recurrence. Completed query
    ingests and result rows remain committed if a later query fails.
    """

    resolved_queries = default_queries(queries)
    run_id = (run_id_factory or (lambda: uuid.uuid4().hex))()
    started_at = utc_now()
    results: list[ScheduledQueryResult] = []
    totals = RunTotals()

    connection = _connect_for_write(db_path)
    try:
        run_history.create_run(
            connection,
            run_id=run_id,
            started_at=started_at,
            trigger=trigger,
            query_count=len(resolved_queries),
        )
        connection.commit()

        for query in resolved_queries:
            query_started_at = utc_now()
            attempts = 1
            try:

                def collect_operation(query: QueryValue = query) -> list[Job]:
                    return collect_jobs(
                        fixture=fixture,
                        live=live,
                        query=query,
                        max_pages=max_pages,
                        page_size=page_size,
                    )

                retry_kwargs: dict[str, Any] = {}
                if sleep is not None:
                    retry_kwargs["sleep"] = sleep
                if jitter is not None:
                    retry_kwargs["jitter"] = jitter
                jobs, attempts = collect_with_retry(collect_operation, **retry_kwargs)
                ingest_result = ingest_records_into_connection(
                    connection,
                    _records_from_jobs(jobs),
                    db_path=db_path,
                    input_path=None,
                    source_query=query,
                )
                query_finished_at = utc_now()
                run_history.insert_run_result(
                    connection,
                    run_id=run_id,
                    query=query,
                    status="success",
                    attempts=attempts,
                    seen_count=ingest_result.seen_count,
                    inserted_count=ingest_result.inserted_count,
                    skipped_count=ingest_result.skipped_count,
                    error_type=None,
                    redacted_error=None,
                    started_at=query_started_at,
                    finished_at=query_finished_at,
                )
                totals = totals.add(
                    seen=ingest_result.seen_count,
                    inserted=ingest_result.inserted_count,
                    skipped=ingest_result.skipped_count,
                )
                results.append(
                    ScheduledQueryResult(
                        query=query,
                        seen_count=ingest_result.seen_count,
                        inserted_count=ingest_result.inserted_count,
                        skipped_count=ingest_result.skipped_count,
                        attempts=attempts,
                    )
                )
                connection.commit()
            except RetryExhausted as exc:
                query_finished_at = utc_now()
                _record_failed_query(
                    connection,
                    run_id=run_id,
                    query=query,
                    attempts=exc.attempts,
                    totals=totals,
                    error=exc.error,
                    started_at=query_started_at,
                    finished_at=query_finished_at,
                )
                connection.commit()
                raise exc.error from exc
            except CollectorError as exc:
                query_finished_at = utc_now()
                _record_failed_query(
                    connection,
                    run_id=run_id,
                    query=query,
                    attempts=1,
                    totals=totals,
                    error=exc,
                    started_at=query_started_at,
                    finished_at=query_finished_at,
                )
                connection.commit()
                raise
            except Exception as exc:
                query_finished_at = utc_now()
                _record_failed_query(
                    connection,
                    run_id=run_id,
                    query=query,
                    attempts=attempts,
                    totals=totals,
                    error=exc,
                    started_at=query_started_at,
                    finished_at=query_finished_at,
                )
                connection.commit()
                raise

        finished_at = utc_now()
        run_history.finish_run_success(
            connection,
            run_id=run_id,
            finished_at=finished_at,
            totals=totals,
        )
        connection.commit()
        return ScheduledCollectionResult(
            db_path=db_path,
            query_count=len(resolved_queries),
            results=tuple(results),
            run_id=run_id,
        )
    except Exception:
        connection.rollback()
        raise
    finally:
        connection.close()
