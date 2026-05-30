from __future__ import annotations

import pytest

from work_feed_mcp.core.errors import ValidationError
from work_feed_mcp.domain.collector_record import validate_payload


def _valid_payload() -> dict[str, object]:
    return {
        "source": "upwork",
        "id": "job-1",
        "title": "Python automation task",
        "description": "Build a small internal automation tool.",
        "url": "https://example.test/jobs/1",
        "skills": ["Python", "Automation"],
    }


@pytest.mark.parametrize(
    "private_field",
    [
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
    ],
)
def test_validate_payload_rejects_private_access_material(private_field: str) -> None:
    payload = _valid_payload()
    payload[private_field] = "secret-value"

    with pytest.raises(ValidationError, match="disallowed private field"):
        validate_payload(payload)


@pytest.mark.parametrize(
    "private_field",
    ["Cookie", "AUTHORIZATION", " Session ", "Proxy_URL"],
)
def test_validate_payload_rejects_private_fields_case_insensitively(
    private_field: str,
) -> None:
    payload = _valid_payload()
    payload[private_field] = "secret-value"

    with pytest.raises(ValidationError, match="disallowed private field"):
        validate_payload(payload)


def test_validate_payload_rejects_unexpected_public_fields() -> None:
    payload = _valid_payload()
    payload["debug_dump"] = {"raw": "unapproved"}

    with pytest.raises(ValidationError, match="unsupported fields: debug_dump"):
        validate_payload(payload)


def test_validate_payload_accepts_canonical_public_record_fields() -> None:
    payload = _valid_payload() | {
        "posted_at": "2026-05-20T00:00:00Z",
        "job_type": "hourly",
        "contractor_tier": "expert",
        "hourly_min": 50,
        "hourly_max": 100.0,
        "fixed_amount": None,
        "raw_id": "raw-1",
    }

    record = validate_payload(payload)

    assert record.job_id == "job-1"
    assert record.source == "upwork"
    assert record.skills == ("python", "automation")
    assert "secret-value" not in record.payload_json
