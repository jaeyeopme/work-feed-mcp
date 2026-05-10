"""Ingest API schemas."""

from __future__ import annotations

from pydantic import BaseModel, ConfigDict, Field

from upwork_app.schemas.collect import CollectRequest


class IngestRequest(BaseModel):
    model_config = ConfigDict(extra="forbid")

    jsonl: str = Field(description="Collector-normalized job JSONL payload.")
    source_query: str | None = None
    run_id: str | None = None


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
