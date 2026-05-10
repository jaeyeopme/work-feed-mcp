from __future__ import annotations

from fastapi import APIRouter

from upwork_app.api.error_mapping import collector_http_error
from upwork_app.integrations.upwork.errors import CollectorError
from upwork_app.schemas.collect import CollectRequest, CollectResponse
from upwork_app.services.collector import collect_jobs

router = APIRouter(prefix="/collect", tags=["collect"])


@router.post("", response_model=CollectResponse)
def collect(request: CollectRequest) -> CollectResponse:
    try:
        jobs = collect_jobs(
            fixture=request.fixture,
            live=request.live,
            query=request.query,
            max_pages=request.max_pages,
            page_size=request.page_size,
        )
    except CollectorError as exc:
        raise collector_http_error(exc) from exc
    return CollectResponse(record_count=len(jobs), jobs=[job.to_dict() for job in jobs])
