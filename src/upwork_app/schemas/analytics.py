"""Analytics API schemas."""

from __future__ import annotations

from typing import Any

from pydantic import BaseModel


class AnalyticsResponse(BaseModel):
    query: str
    rows: list[dict[str, Any]]
