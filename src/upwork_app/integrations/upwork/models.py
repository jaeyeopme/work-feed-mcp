"""JSONL-safe data models."""

from __future__ import annotations

from dataclasses import asdict, dataclass
from typing import Any


@dataclass(frozen=True, slots=True)
class Job:
    source: str
    id: str
    title: str
    description: str
    url: str
    skills: list[str]
    posted_at: str | None = None
    job_type: str | None = None
    contractor_tier: str | None = None
    hourly_min: float | None = None
    hourly_max: float | None = None
    fixed_amount: float | None = None
    raw_id: str | None = None

    def to_dict(self) -> dict[str, Any]:
        data = asdict(self)
        data["skills"] = list(self.skills)
        return data
