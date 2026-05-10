"""Live HTTP transport kept behind a narrow boundary."""

from __future__ import annotations

import json
import os
import re
import urllib.error
import urllib.request
from http.cookiejar import CookieJar
from typing import Any

from upwork_collector.credentials import load_credential_references, redact
from upwork_collector.errors import (
    CredentialRequiredError,
    RateLimitedError,
    UpstreamBlockedError,
    UpstreamSchemaOrTemporaryError,
)
from upwork_collector.graphql import ENDPOINT, build_request_payload

USER_AGENT = (
    "Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) "
    "AppleWebKit/537.36 (KHTML, like Gecko) Chrome/124.0.0.0 Safari/537.36"
)
_VISITOR_TOKEN_PATTERN = re.compile(r"(?i)(?:^|[;\s])visitor_gql_token=([^;\s]+)")


def require_live_enabled(env: dict[str, str] | None = None) -> None:
    source = os.environ if env is None else env
    if source.get("UPWORK_COLLECTOR_LIVE") != "1":
        raise CredentialRequiredError("live collection requires UPWORK_COLLECTOR_LIVE=1")


def _extract_visitor_token(cookie_jar: CookieJar, cookie_header: str = "") -> str | None:
    for cookie in cookie_jar:
        if cookie.name == "visitor_gql_token" and cookie.value:
            return cookie.value
    match = _VISITOR_TOKEN_PATTERN.search(cookie_header)
    if match:
        return match.group(1)
    return None


def classify_http_status(status: int, body: str = "") -> None:
    lowered = body.lower()
    if status in {401, 403} or "access denied" in lowered or "forbidden" in lowered:
        raise UpstreamBlockedError("upstream blocked or denied the request")
    if status == 429 or "rate limit" in lowered or "throttle" in lowered:
        raise RateLimitedError("upstream rate limited the request")
    if status >= 500:
        raise UpstreamSchemaOrTemporaryError("upstream temporary server failure")


def collect_live(
    query: str | None, *, max_pages: int = 1, page_size: int = 50
) -> list[dict[str, Any]]:
    require_live_enabled()
    credentials = load_credential_references()
    cookie_jar = CookieJar()
    handlers: list[urllib.request.BaseHandler] = [urllib.request.HTTPCookieProcessor(cookie_jar)]
    if credentials.proxy_url:
        handlers.append(
            urllib.request.ProxyHandler(
                {"http": credentials.proxy_url.value, "https": credentials.proxy_url.value}
            )
        )
    opener = urllib.request.build_opener(*handlers)
    headers = {
        "User-Agent": USER_AGENT,
        "Accept": "application/json",
        "Accept-Language": "en-US,en;q=0.9",
        "Origin": "https://www.upwork.com",
        "Referer": "https://www.upwork.com/",
    }
    cookie_values = [
        secret.value for secret in (credentials.cookie, credentials.session) if secret is not None
    ]
    cookie_header = "; ".join(cookie_values)
    if cookie_header:
        headers["Cookie"] = cookie_header

    try:
        bootstrap_headers = {
            **headers,
            "Accept": "text/html,application/xhtml+xml,application/xml;q=0.9,*/*;q=0.8",
        }
        opener.open(
            urllib.request.Request("https://www.upwork.com/", headers=bootstrap_headers), timeout=20
        )
        visitor_token = _extract_visitor_token(cookie_jar, cookie_header)
        if visitor_token:
            headers["Authorization"] = f"Bearer {visitor_token}"
        all_results: list[dict[str, Any]] = []
        for page in range(max_pages):
            payload = build_request_payload(query, offset=page * page_size, count=page_size)
            body = json.dumps(payload).encode("utf-8")
            request = urllib.request.Request(
                ENDPOINT,
                data=body,
                headers={**headers, "Content-Type": "application/json"},
                method="POST",
            )
            with opener.open(request, timeout=30) as response:
                text = response.read().decode("utf-8")
                classify_http_status(response.status, text)
                decoded = json.loads(text)
                if not isinstance(decoded, dict):
                    raise UpstreamSchemaOrTemporaryError(
                        "upstream GraphQL response is not an object"
                    )
                all_results.append(decoded)
        return all_results
    except urllib.error.HTTPError as exc:
        text = exc.read().decode("utf-8", errors="replace")
        classify_http_status(exc.code, text)
        raise UpstreamSchemaOrTemporaryError(redact(f"upstream HTTP failure: {exc.code}")) from exc
    except urllib.error.URLError as exc:
        raise UpstreamSchemaOrTemporaryError(
            redact(f"upstream network failure: {exc.reason}")
        ) from exc
    except json.JSONDecodeError as exc:
        raise UpstreamSchemaOrTemporaryError("upstream returned non-JSON response") from exc
