"""Ingest API schemas."""

from __future__ import annotations

from pydantic import BaseModel, ConfigDict, Field, model_validator

from upwork_app.schemas.collect import CollectRequest


class IngestRequest(BaseModel):
    model_config = ConfigDict(extra="forbid")

    jsonl: str | None = Field(default=None, description="Collector-normalized job JSONL payload.")
    jobs: list[dict[str, object]] | None = Field(
        default=None, description="Collector-normalized job objects. Preferred for HTTP clients."
    )
    source_query: str | None = None
    run_id: str | None = None

    @model_validator(mode="after")
    def require_exactly_one_payload(self) -> IngestRequest:
        has_jsonl = self.jsonl is not None
        has_jobs = self.jobs is not None
        if has_jsonl == has_jobs:
            raise ValueError("provide exactly one of jsonl or jobs")
        return self


class IngestResponse(BaseModel):
    run_id: str
    record_count: int
    input_path: str | None
    source_query: str | None


class CollectAndIngestRequest(BaseModel):
    model_config = ConfigDict(extra="forbid")

    collect: CollectRequest
    source_query: str | None = None
    run_id: str | None = None
