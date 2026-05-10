from __future__ import annotations

from typing import Literal

from fastapi import APIRouter

from upwork_app.api.error_mapping import collector_http_error
from upwork_app.integrations.upwork.errors import CollectorError
from upwork_app.integrations.upwork.models import Job
from upwork_app.schemas.collect import CollectJobsResponse, CollectRequest, CollectSummaryResponse
from upwork_app.services.collector import collect_jobs

router = APIRouter(prefix="/collect", tags=["collect"])


def _collect(request: CollectRequest) -> list[Job]:
    try:
        return collect_jobs(
            fixture=request.fixture,
            live=request.live,
            query=request.query,
            max_pages=request.max_pages,
            page_size=request.page_size,
        )
    except CollectorError as exc:
        raise collector_http_error(exc) from exc


def _source(request: CollectRequest) -> Literal["fixture", "live"]:
    return "live" if request.live else "fixture"


@router.post("", response_model=CollectSummaryResponse)
def collect(request: CollectRequest) -> CollectSummaryResponse:
    jobs = _collect(request)
    return CollectSummaryResponse(
        record_count=len(jobs), query=request.query, source=_source(request)
    )


@router.post("/jobs", response_model=CollectJobsResponse)
def collect_jobs_preview(request: CollectRequest) -> CollectJobsResponse:
    jobs = _collect(request)
    return CollectJobsResponse(
        record_count=len(jobs),
        query=request.query,
        source=_source(request),
        jobs=[job.to_dict() for job in jobs],
    )
