"""Collection request/response schemas."""

from __future__ import annotations

from typing import Any

from pydantic import BaseModel, ConfigDict, Field


class CollectRequest(BaseModel):
    model_config = ConfigDict(extra="forbid")

    fixture: str | None = None
    live: bool = False
    query: str | None = None
    max_pages: int = Field(default=1, ge=1, le=5)
    page_size: int = Field(default=50, ge=1, le=50)


class CollectResponse(BaseModel):
    record_count: int
    jobs: list[dict[str, Any]]
