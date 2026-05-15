from __future__ import annotations

import pytest
from tests.conftest import load_fixture

from work_feed_mcp.integrations.upwork.errors import UpstreamSchemaOrTemporaryError
from work_feed_mcp.integrations.upwork.normalize import normalize_response


def test_normalizes_representative_graphql_response() -> None:
    jobs = normalize_response(load_fixture("visitor_job_search_response.json"))

    assert len(jobs) == 2
    first = jobs[0].to_dict()
    assert first["source"] == "upwork"
    assert first["id"] == "cipher-job-1"
    assert first["raw_id"] == "raw-job-1"
    assert first["title"] == "Python Data Collector"
    assert first["description"]
    assert first["url"].endswith("/cipher-job-1")
    assert first["skills"] == ["Python", "Data Scraping"]
    for key in [
        "posted_at",
        "job_type",
        "contractor_tier",
        "hourly_min",
        "hourly_max",
        "fixed_amount",
        "raw_id",
    ]:
        assert key in first


def test_missing_optional_fields_are_safe() -> None:
    job = normalize_response(load_fixture("missing_optional_fields_response.json"))[0]

    assert job.skills == []
    assert job.hourly_min is None
    assert job.hourly_max is None
    assert job.fixed_amount is None
    assert job.contractor_tier is None


def test_missing_required_identity_fails_closed() -> None:
    with pytest.raises(UpstreamSchemaOrTemporaryError):
        normalize_response(load_fixture("missing_identity_response.json"))


def test_malformed_response_shape_fails_closed() -> None:
    with pytest.raises(UpstreamSchemaOrTemporaryError):
        normalize_response(load_fixture("malformed_response.json"))


def test_graphql_errors_fail_closed() -> None:
    with pytest.raises(UpstreamSchemaOrTemporaryError):
        normalize_response(load_fixture("graphql_errors_response.json"))


def test_live_numeric_id_without_ciphertext_builds_permalink() -> None:
    response = {
        "data": {
            "search": {
                "universalSearchNuxt": {
                    "visitorJobSearchV1": {
                        "results": [
                            {
                                "id": "2053400105465582222",
                                "title": "Live Shape",
                                "description": "Current visitor search result shape.",
                            }
                        ]
                    }
                }
            }
        }
    }

    job = normalize_response(response)[0]

    assert job.id == "~022053400105465582222"
    assert job.url == "https://www.upwork.com/jobs/~022053400105465582222"
    assert job.raw_id == "2053400105465582222"


def test_raw_id_without_ciphertext_fails_closed() -> None:
    response = {
        "data": {
            "search": {
                "universalSearchNuxt": {
                    "visitorJobSearchV1": {
                        "results": [
                            {
                                "id": "raw-only",
                                "title": "Raw Identity Only",
                                "description": "URL cannot be trusted without ciphertext.",
                                "skills": [],
                            }
                        ]
                    }
                }
            }
        }
    }

    with pytest.raises(UpstreamSchemaOrTemporaryError):
        normalize_response(response)


def test_legacy_live_job_tile_shape_maps_details() -> None:
    job = normalize_response(load_fixture("live_job_tile_response.json"))[0]

    assert job.id == "~022053400105465582222"
    assert job.skills == ["Python", "API Integration"]
    assert job.job_type == "HOURLY"
    assert job.hourly_min == 25.0
    assert job.hourly_max == 45.0
    assert job.fixed_amount == 500.0
    assert job.posted_at == "2026-05-01T00:00:00Z"
    assert job.contractor_tier == "INTERMEDIATE"
