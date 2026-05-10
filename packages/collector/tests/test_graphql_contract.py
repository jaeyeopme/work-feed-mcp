from __future__ import annotations

import pytest

from tests.conftest import load_fixture
from upwork_collector.errors import UpstreamSchemaOrTemporaryError
from upwork_collector.graphql import ENDPOINT, build_request_payload, extract_results


def test_graphql_endpoint_contract() -> None:
    assert ENDPOINT == "https://www.upwork.com/api/graphql/v1"


def test_graphql_request_variables_contract() -> None:
    payload = build_request_payload("python", offset=10, count=5)

    assert payload["variables"] == {
        "request": {"paging": {"offset": 10, "count": 5}, "userQuery": "python"}
    }
    assert "budget" not in str(payload["variables"]).lower()


def test_graphql_request_omits_empty_query() -> None:
    payload = build_request_payload(None, offset=0, count=10)

    assert payload["variables"] == {"request": {"paging": {"offset": 0, "count": 10}}}


def test_extractor_reads_expected_results_path() -> None:
    results = extract_results(load_fixture("visitor_job_search_response.json"))
    assert len(results) == 2


def test_graphql_errors_raise_typed_error() -> None:
    with pytest.raises(UpstreamSchemaOrTemporaryError):
        extract_results(load_fixture("graphql_errors_response.json"))
