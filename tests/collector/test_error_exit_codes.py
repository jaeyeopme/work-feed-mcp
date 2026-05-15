from __future__ import annotations

import pytest

from work_feed_mcp.integrations.upwork.errors import (
    CredentialRequiredError,
    ExitCode,
    InternalFailureError,
    RateLimitedError,
    UpstreamBlockedError,
    UpstreamSchemaOrTemporaryError,
    UsageError,
    exit_code_for_error,
)
from work_feed_mcp.integrations.upwork.transport import classify_http_status


def test_typed_errors_map_to_stable_exit_codes() -> None:
    assert exit_code_for_error(UsageError("bad args")) == ExitCode.USAGE_ERROR
    assert exit_code_for_error(CredentialRequiredError()) == ExitCode.CREDENTIAL_REQUIRED
    assert exit_code_for_error(UpstreamBlockedError()) == ExitCode.UPSTREAM_BLOCKED
    assert exit_code_for_error(RateLimitedError()) == ExitCode.RATE_LIMITED
    assert (
        exit_code_for_error(UpstreamSchemaOrTemporaryError())
        == ExitCode.UPSTREAM_SCHEMA_OR_TEMPORARY_FAILURE
    )
    assert exit_code_for_error(InternalFailureError()) == ExitCode.INTERNAL_FAILURE
    assert exit_code_for_error(RuntimeError("boom")) == ExitCode.INTERNAL_FAILURE


def test_synthetic_status_classification_for_block_and_rate_limit() -> None:
    with pytest.raises(UpstreamBlockedError) as blocked:
        classify_http_status(403, "forbidden")
    assert blocked.value.code == ExitCode.UPSTREAM_BLOCKED

    with pytest.raises(RateLimitedError) as limited:
        classify_http_status(429, "rate limit")
    assert limited.value.code == ExitCode.RATE_LIMITED


def test_synthetic_status_classification_allows_success_status() -> None:
    assert classify_http_status(200, "ok") is None
