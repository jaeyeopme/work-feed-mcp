from __future__ import annotations

import json
from typing import Any

import pytest

from work_feed_mcp.integrations.upwork import transport
from work_feed_mcp.integrations.upwork.credentials import CredentialReferences, SecretValue
from work_feed_mcp.integrations.upwork.errors import (
    CredentialRequiredError,
    RateLimitedError,
    UpstreamBlockedError,
    UpstreamSchemaOrTemporaryError,
)


class FakeResponse:
    def __init__(
        self,
        *,
        status_code: int = 200,
        text: str = "{}",
        json_data: object = None,
        json_error: json.JSONDecodeError | None = None,
        cookies: dict[str, object] | None = None,
    ) -> None:
        self.status_code = status_code
        self._text = text
        self._json_data = {} if json_data is None else json_data
        self._json_error = json_error
        self.cookies = {} if cookies is None else cookies
        self.content = text.encode()

    @property
    def text(self) -> str:
        return self._text

    def json(self) -> object:
        if self._json_error is not None:
            raise self._json_error
        return self._json_data


def test_success_status_does_not_scan_job_text_for_rate_limit_words() -> None:
    transport.classify_http_status(200, "job description mentions API rate limits")
    transport.classify_http_status(200, "job description mentions throttled API integrations")


def test_error_status_body_can_refine_classification() -> None:
    with pytest.raises(RateLimitedError):
        transport.classify_http_status(429, "too many requests")
    with pytest.raises(UpstreamBlockedError):
        transport.classify_http_status(403, "forbidden")
    with pytest.raises(UpstreamSchemaOrTemporaryError):
        transport.classify_http_status(503, "maintenance")


def test_require_live_enabled_uses_explicit_env_gate() -> None:
    with pytest.raises(CredentialRequiredError, match="WORK_FEED_LIVE=1"):
        transport.require_live_enabled({})

    assert transport.require_live_enabled({"WORK_FEED_LIVE": "1"}) is None


def test_collect_live_builds_paged_requests_without_real_network(
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    proxy = "http://user:pass@example.test:8080"
    get_calls: list[dict[str, object]] = []
    post_calls: list[dict[str, Any]] = []
    sleep_calls: list[float] = []

    def fake_get(
        url: str, *, impersonate: str, proxies: dict[str, str] | None, timeout: int
    ) -> FakeResponse:
        get_calls.append(
            {
                "url": url,
                "impersonate": impersonate,
                "proxies": proxies,
                "timeout": timeout,
            }
        )
        return FakeResponse(cookies={"visitor_gql_token": "visitor-token"})

    def fake_post(
        url: str,
        *,
        headers: dict[str, str],
        json: dict[str, Any],
        impersonate: str,
        proxies: dict[str, str] | None,
        timeout: int,
    ) -> FakeResponse:
        post_calls.append(
            {
                "url": url,
                "headers": dict(headers),
                "json": json,
                "impersonate": impersonate,
                "proxies": proxies,
                "timeout": timeout,
            }
        )
        return FakeResponse(json_data={"page": len(post_calls)})

    monkeypatch.setenv("WORK_FEED_LIVE", "1")
    monkeypatch.setattr(
        transport,
        "load_credential_references",
        lambda: CredentialReferences(proxy_url=SecretValue("proxy_url", proxy)),
    )
    monkeypatch.setattr(transport.curl_requests, "get", fake_get)
    monkeypatch.setattr(transport.curl_requests, "post", fake_post)
    monkeypatch.setattr(transport.random, "uniform", lambda start, end: 2.25)
    monkeypatch.setattr(transport.time, "sleep", sleep_calls.append)

    results = transport.collect_live("python", max_pages=2, page_size=25)

    assert results == [{"page": 1}, {"page": 2}]
    assert get_calls == [
        {
            "url": "https://www.upwork.com/",
            "impersonate": "chrome",
            "proxies": {"http": proxy, "https": proxy},
            "timeout": 30,
        }
    ]
    assert sleep_calls == [2.25]
    assert [call["json"]["variables"]["requestVariables"]["paging"] for call in post_calls] == [
        {"offset": 0, "count": 25},
        {"offset": 25, "count": 25},
    ]
    for call in post_calls:
        assert call["url"] == transport.ENDPOINT
        assert call["headers"]["Authorization"] == "Bearer visitor-token"
        assert call["impersonate"] == "chrome"
        assert call["proxies"] == {"http": proxy, "https": proxy}
        assert call["timeout"] == 30


def test_collect_live_classifies_blocked_bootstrap_status(
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    monkeypatch.setenv("WORK_FEED_LIVE", "1")
    monkeypatch.setattr(
        transport,
        "load_credential_references",
        lambda: CredentialReferences(),
    )
    monkeypatch.setattr(
        transport.curl_requests,
        "get",
        lambda *args, **kwargs: FakeResponse(status_code=403, text="forbidden"),
    )

    with pytest.raises(UpstreamBlockedError):
        transport.collect_live("python")


def test_collect_live_redacts_network_failure_diagnostics(
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    proxy = "http://user:pass@example.test:8080"

    def fake_post(*args: object, **kwargs: object) -> FakeResponse:
        raise transport.curl_requests.exceptions.RequestException(
            "proxy=http://user:pass@example.test:8080 "
            "visitor_gql_token=secret-token Bearer secret-token"
        )

    monkeypatch.setenv("WORK_FEED_LIVE", "1")
    monkeypatch.setenv("WORK_FEED_PROXY_URL", proxy)
    monkeypatch.setattr(
        transport.curl_requests,
        "get",
        lambda *args, **kwargs: FakeResponse(cookies={"visitor_gql_token": "visitor-token"}),
    )
    monkeypatch.setattr(transport.curl_requests, "post", fake_post)

    with pytest.raises(UpstreamSchemaOrTemporaryError) as raised:
        transport.collect_live("python")

    message = str(raised.value)
    assert "user:pass" not in message
    assert "secret-token" not in message
    assert "<redacted>" in message
