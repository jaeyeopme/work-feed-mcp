"""One-shot scheduled collection orchestration for OS schedulers."""

from __future__ import annotations

from dataclasses import asdict, dataclass
from typing import Any

from upwork_app.domain.collector_record import CollectorRecord, validate_payload
from upwork_app.integrations.upwork.models import Job
from upwork_app.services.collector import collect_jobs
from upwork_app.services.ingestion import ingest_records


@dataclass(frozen=True, slots=True)
class ScheduledQueryResult:
    query: str
    seen_count: int
    inserted_count: int
    skipped_count: int

    def to_dict(self) -> dict[str, Any]:
        return asdict(self)


@dataclass(frozen=True, slots=True)
class ScheduledCollectionResult:
    db_path: str
    query_count: int
    results: tuple[ScheduledQueryResult, ...]

    def to_dict(self) -> dict[str, Any]:
        return {
            "db_path": self.db_path,
            "query_count": self.query_count,
            "results": [result.to_dict() for result in self.results],
        }


def parse_queries(value: str) -> tuple[str, ...]:
    """Parse comma-separated query option text."""

    queries = tuple(part.strip() for part in value.split(",") if part.strip())
    if not queries:
        raise ValueError("--queries must contain at least one query")
    return queries


def _records_from_jobs(jobs: list[Job]) -> list[CollectorRecord]:
    return [validate_payload(job.to_dict()) for job in jobs]


def collect_scheduled(
    *,
    db_path: str,
    queries: tuple[str, ...],
    max_pages: int = 1,
    page_size: int = 50,
) -> ScheduledCollectionResult:
    """Collect and ingest multiple live queries sequentially.

    This is intentionally one-shot: systemd/cron owns recurrence. The function
    fails fast on the first query error; previously completed query ingests stay
    committed by the ingestion layer.
    """

    results: list[ScheduledQueryResult] = []
    for query in queries:
        jobs = collect_jobs(live=True, query=query, max_pages=max_pages, page_size=page_size)
        ingest_result = ingest_records(
            _records_from_jobs(jobs),
            db_path=db_path,
            input_path=None,
            source_query=query,
        )
        results.append(
            ScheduledQueryResult(
                query=query,
                seen_count=ingest_result.seen_count,
                inserted_count=ingest_result.inserted_count,
                skipped_count=ingest_result.skipped_count,
            )
        )
    return ScheduledCollectionResult(
        db_path=db_path,
        query_count=len(queries),
        results=tuple(results),
    )
