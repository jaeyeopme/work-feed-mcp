"""Collector record validation and canonicalization."""

from __future__ import annotations

import hashlib
import json
from dataclasses import dataclass
from typing import Any

from work_feed_mcp.core.errors import ValidationError

_REQUIRED_STRING_FIELDS = ("source", "id", "title", "description", "url")
_OPTIONAL_STRING_FIELDS = ("posted_at", "job_type", "contractor_tier", "raw_id")
_OPTIONAL_NUMBER_FIELDS = ("hourly_min", "hourly_max", "fixed_amount")
_ALLOWED_FIELDS = frozenset(
    (*_REQUIRED_STRING_FIELDS, "skills", *_OPTIONAL_STRING_FIELDS, *_OPTIONAL_NUMBER_FIELDS)
)
_SECRET_FIELD_NAMES = frozenset(
    {
        "cookie",
        "cookies",
        "authorization",
        "session",
        "session_id",
        "token",
        "access_token",
        "proxy",
        "proxy_url",
        "graphql_response",
        "raw_graphql_response",
    }
)


@dataclass(frozen=True, slots=True)
class CollectorRecord:
    payload: dict[str, Any]
    payload_json: str
    content_hash: str
    job_id: str
    source: str
    title: str
    description: str
    url: str
    skills: tuple[str, ...]
    posted_at: str | None
    job_type: str | None
    contractor_tier: str | None
    hourly_min: float | None
    hourly_max: float | None
    fixed_amount: float | None
    raw_id: str | None


def canonical_payload_json(payload: dict[str, Any]) -> str:
    return json.dumps(payload, ensure_ascii=False, sort_keys=True, separators=(",", ":"))


def content_hash_for_payload_json(payload_json: str) -> str:
    return hashlib.sha256(payload_json.encode("utf-8")).hexdigest()


def _require_string(payload: dict[str, Any], key: str) -> str:
    value = payload.get(key)
    if not isinstance(value, str) or not value.strip():
        raise ValidationError(f"record missing required collector field: {key}")
    return value.strip()


def _optional_string(payload: dict[str, Any], key: str) -> str | None:
    value = payload.get(key)
    if value is None:
        return None
    if not isinstance(value, str):
        raise ValidationError(f"collector field must be string or null: {key}")
    stripped = value.strip()
    return stripped or None


def _optional_number(payload: dict[str, Any], key: str) -> float | None:
    value = payload.get(key)
    if value is None:
        return None
    if isinstance(value, bool) or not isinstance(value, int | float):
        raise ValidationError(f"collector field must be numeric or null: {key}")
    return float(value)


def _skills(payload: dict[str, Any]) -> tuple[str, ...]:
    value = payload.get("skills")
    if not isinstance(value, list):
        raise ValidationError("record missing required collector field: skills")
    normalized: list[str] = []
    seen: set[str] = set()
    for item in value:
        if not isinstance(item, str):
            raise ValidationError("collector field must be list[string]: skills")
        skill = " ".join(item.strip().split()).casefold()
        if skill and skill not in seen:
            seen.add(skill)
            normalized.append(skill)
    return tuple(normalized)


def _assert_no_private_payload_fields(payload: dict[str, Any]) -> None:
    for key in payload:
        normalized = key.strip().casefold()
        if normalized in _SECRET_FIELD_NAMES:
            raise ValidationError(f"collector payload contains disallowed private field: {key}")
    unexpected = set(payload) - _ALLOWED_FIELDS
    if unexpected:
        joined = ", ".join(sorted(unexpected))
        raise ValidationError(f"collector payload contains unsupported fields: {joined}")


def validate_payload(payload: object) -> CollectorRecord:
    if not isinstance(payload, dict):
        raise ValidationError("JSONL line must contain a JSON object")
    _assert_no_private_payload_fields(payload)
    source = _require_string(payload, "source")
    if source != "upwork":
        raise ValidationError("collector field source must be 'upwork'")
    payload_json = canonical_payload_json(payload)
    return CollectorRecord(
        payload=payload,
        payload_json=payload_json,
        content_hash=content_hash_for_payload_json(payload_json),
        job_id=_require_string(payload, "id"),
        source=source,
        title=_require_string(payload, "title"),
        description=_require_string(payload, "description"),
        url=_require_string(payload, "url"),
        skills=_skills(payload),
        posted_at=_optional_string(payload, "posted_at"),
        job_type=_optional_string(payload, "job_type"),
        contractor_tier=_optional_string(payload, "contractor_tier"),
        hourly_min=_optional_number(payload, "hourly_min"),
        hourly_max=_optional_number(payload, "hourly_max"),
        fixed_amount=_optional_number(payload, "fixed_amount"),
        raw_id=_optional_string(payload, "raw_id"),
    )
