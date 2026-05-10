"""HTTP error mapping for expected application errors."""

from __future__ import annotations

from fastapi import HTTPException

from upwork_app.core.errors import ExitCode as IngestExitCode
from upwork_app.core.errors import IngestError
from upwork_app.integrations.upwork.credentials import redact
from upwork_app.integrations.upwork.errors import CollectorError
from upwork_app.integrations.upwork.errors import ExitCode as CollectorExitCode

_COLLECTOR_STATUS_BY_CODE: dict[CollectorExitCode, int] = {
    CollectorExitCode.USAGE_ERROR: 400,
    CollectorExitCode.CREDENTIAL_REQUIRED: 401,
    CollectorExitCode.UPSTREAM_BLOCKED: 502,
    CollectorExitCode.RATE_LIMITED: 429,
    CollectorExitCode.UPSTREAM_SCHEMA_OR_TEMPORARY_FAILURE: 503,
    CollectorExitCode.INTERNAL_FAILURE: 500,
}

_INGEST_STATUS_BY_CODE: dict[IngestExitCode, int] = {
    IngestExitCode.USAGE_ERROR: 400,
    IngestExitCode.VALIDATION_ERROR: 422,
    IngestExitCode.INTERNAL_FAILURE: 500,
}


def collector_http_error(error: CollectorError) -> HTTPException:
    status_code = _COLLECTOR_STATUS_BY_CODE.get(error.code, 500)
    detail = "collector internal failure" if status_code >= 500 else redact(error)
    if error.code in {
        CollectorExitCode.UPSTREAM_BLOCKED,
        CollectorExitCode.UPSTREAM_SCHEMA_OR_TEMPORARY_FAILURE,
    }:
        detail = redact(error)
    return HTTPException(status_code=status_code, detail=detail)


def ingest_http_error(error: IngestError) -> HTTPException:
    status_code = _INGEST_STATUS_BY_CODE.get(error.code, 500)
    detail = "ingest internal failure" if status_code >= 500 else str(error)
    return HTTPException(status_code=status_code, detail=detail)
