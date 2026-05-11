from __future__ import annotations

from dataclasses import asdict
from io import StringIO

from fastapi import APIRouter, Depends

from upwork_app.api.deps import settings
from upwork_app.api.error_mapping import collector_http_error, ingest_http_error
from upwork_app.core.config import Settings
from upwork_app.core.errors import IngestError
from upwork_app.domain.collector_record import validate_payload
from upwork_app.integrations.upwork.errors import CollectorError
from upwork_app.schemas.ingest import CollectAndIngestRequest, IngestRequest, IngestResponse
from upwork_app.services.collector import collect_jobs, jobs_to_jsonl
from upwork_app.services.ingestion import ingest_records, read_jsonl

settings_dependency = Depends(settings)

router = APIRouter(tags=["ingest"])
runs_router = APIRouter(prefix="/runs", tags=["runs"])


@router.post("/ingest", response_model=IngestResponse)
def ingest(request: IngestRequest, app_settings: Settings = settings_dependency) -> IngestResponse:
    try:
        if request.jobs is not None:
            records = [validate_payload(job) for job in request.jobs]
        else:
            assert request.jsonl is not None
            records = read_jsonl(StringIO(request.jsonl))
        result = ingest_records(
            records,
            db_path=app_settings.default_db_path,
            input_path=None,
            source_query=request.source_query,
        )
    except IngestError as exc:
        raise ingest_http_error(exc) from exc
    return IngestResponse.model_validate(asdict(result))


@router.post("/collect-and-ingest", response_model=IngestResponse)
def collect_and_ingest(
    request: CollectAndIngestRequest, app_settings: Settings = settings_dependency
) -> IngestResponse:
    try:
        jobs = collect_jobs(
            fixture=request.collect.fixture,
            live=request.collect.live,
            query=request.collect.query,
            max_pages=request.collect.max_pages,
            page_size=request.collect.page_size,
        )
        records = read_jsonl(StringIO(jobs_to_jsonl(jobs)))
        result = ingest_records(
            records,
            db_path=app_settings.default_db_path,
            input_path=None,
            source_query=request.source_query or request.collect.query,
        )
    except CollectorError as exc:
        raise collector_http_error(exc) from exc
    except IngestError as exc:
        raise ingest_http_error(exc) from exc
    return IngestResponse.model_validate(asdict(result))


@runs_router.post("/collect", response_model=IngestResponse)
def create_collect_run(
    request: CollectAndIngestRequest, app_settings: Settings = settings_dependency
) -> IngestResponse:
    return collect_and_ingest(request, app_settings)
