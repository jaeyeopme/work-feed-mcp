from __future__ import annotations

import pytest

from upwork_app.integrations.upwork.errors import (
    RateLimitedError,
    UpstreamBlockedError,
    UpstreamSchemaOrTemporaryError,
)
from upwork_app.integrations.upwork.transport import (
    _read_response_text,
    classify_http_status,
)


def test_success_status_does_not_scan_job_text_for_rate_limit_words() -> None:
    classify_http_status(200, "job description mentions API rate limits")
    classify_http_status(200, "job description mentions throttled API integrations")


def test_error_status_body_can_refine_classification() -> None:
    with pytest.raises(RateLimitedError):
        classify_http_status(429, "too many requests")
    with pytest.raises(UpstreamBlockedError):
        classify_http_status(403, "forbidden")
    with pytest.raises(UpstreamSchemaOrTemporaryError):
        classify_http_status(503, "maintenance")


def test_decode_fallback_text_is_bounded_to_response_body() -> None:
    class Response:
        @property
        def text(self) -> str:
            raise UnicodeDecodeError("utf-8", b"\xff", 0, 1, "bad byte")

        content = b"non-json body"

    assert _read_response_text(Response()) == "non-json body"
