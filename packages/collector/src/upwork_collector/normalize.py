"""Normalize Upwork GraphQL responses into JSONL-safe job records."""

from __future__ import annotations

from typing import Any

from upwork_collector.errors import UpstreamSchemaOrTemporaryError
from upwork_collector.graphql import extract_results
from upwork_collector.models import Job


def _first_text(*values: object) -> str | None:
    for value in values:
        if isinstance(value, str) and value.strip():
            return value.strip()
    return None


def _number(value: object) -> float | None:
    if isinstance(value, int | float) and not isinstance(value, bool):
        return float(value)
    return None


def _skills(raw: object) -> list[str]:
    if not isinstance(raw, list):
        return []
    names: list[str] = []
    for item in raw:
        if isinstance(item, str) and item.strip():
            names.append(item.strip())
        elif isinstance(item, dict):
            name = _first_text(item.get("name"), item.get("prettyName"), item.get("skill"))
            if name:
                names.append(name)
    return names


def _budget_amount(raw: object, *keys: str) -> float | None:
    if not isinstance(raw, dict):
        return None
    for key in keys:
        number = _number(raw.get(key))
        if number is not None:
            return number
    return None


def normalize_result(raw: dict[str, Any]) -> Job:
    job = raw.get("job") if isinstance(raw.get("job"), dict) else {}
    assert isinstance(job, dict)

    raw_id = _first_text(raw.get("id"), raw.get("uid"), job.get("id"))
    cipher = _first_text(
        raw.get("cipherText"),
        raw.get("ciphertext"),
        job.get("cipherText"),
        job.get("ciphertext"),
    )
    if not raw_id:
        raise UpstreamSchemaOrTemporaryError("job result missing required raw identity field")
    if cipher:
        job_id = cipher
    elif raw_id.isdecimal():
        job_id = f"~02{raw_id}"
    else:
        raise UpstreamSchemaOrTemporaryError("job result missing required ciphertext for permalink")

    title = _first_text(raw.get("title"), job.get("title"))
    description = _first_text(raw.get("description"), raw.get("snippet"), job.get("description"))
    if not title or not description:
        raise UpstreamSchemaOrTemporaryError("job result missing title or description")

    skills = _skills(raw.get("skills") if raw.get("skills") is not None else job.get("skills"))
    hourly = (
        raw.get("hourlyBudget") if raw.get("hourlyBudget") is not None else job.get("hourlyBudget")
    )
    fixed = (
        raw.get("fixedPriceBudget")
        if raw.get("fixedPriceBudget") is not None
        else job.get("fixedPriceBudget")
    )

    return Job(
        source="upwork",
        id=job_id,
        title=title,
        description=description,
        url=f"https://www.upwork.com/jobs/{job_id}",
        skills=skills,
        posted_at=_first_text(raw.get("postedOn"), raw.get("posted_at"), job.get("postedOn")),
        job_type=_first_text(raw.get("jobType"), raw.get("job_type"), job.get("jobType")),
        contractor_tier=_first_text(
            raw.get("contractorTier"), raw.get("contractor_tier"), job.get("contractorTier")
        ),
        hourly_min=_budget_amount(hourly, "min", "hourly_min"),
        hourly_max=_budget_amount(hourly, "max", "hourly_max"),
        fixed_amount=_budget_amount(fixed, "amount", "fixed_amount"),
        raw_id=raw_id,
    )


def normalize_response(response: dict[str, Any]) -> list[Job]:
    return [normalize_result(item) for item in extract_results(response)]
