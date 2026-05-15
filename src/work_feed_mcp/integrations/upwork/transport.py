"""Live HTTP transport kept behind a narrow boundary."""

from __future__ import annotations

import json
import os
import random
import time
from typing import Any, cast

from curl_cffi import requests as curl_requests

from work_feed_mcp.integrations.upwork.credentials import load_credential_references, redact
from work_feed_mcp.integrations.upwork.errors import (
    CollectorError,
    CredentialRequiredError,
    RateLimitedError,
    UpstreamBlockedError,
    UpstreamSchemaOrTemporaryError,
)
from work_feed_mcp.integrations.upwork.graphql import ENDPOINT, build_request_payload

HEADERS = {
    "Accept": "*/*",
    "Accept-Language": "en-US,en;q=0.9",
    "Accept-Encoding": "gzip",
    "Referer": "https://www.upwork.com/nx/search/jobs/",
    "X-Upwork-Accept-Language": "en-US",
    "Content-Type": "application/json",
}


def require_live_enabled(env: dict[str, str] | None = None) -> None:
    source = os.environ if env is None else env
    if source.get("WORK_FEED_LIVE") != "1":
        raise CredentialRequiredError("live collection requires WORK_FEED_LIVE=1")


def classify_http_status(status: int, body: str = "") -> None:
    lowered = body.lower()
    if 200 <= status < 300:
        return
    if status in {401, 403} or "access denied" in lowered or "forbidden" in lowered:
        raise UpstreamBlockedError("upstream blocked or denied the request")
    if status == 429 or "rate limit" in lowered or "throttle" in lowered:
        raise RateLimitedError("upstream rate limited the request")
    if status >= 500:
        raise UpstreamSchemaOrTemporaryError("upstream temporary server failure")


def _read_response_text(response: curl_requests.Response) -> str:
    try:
        return response.text
    except UnicodeDecodeError:
        return response.content.decode("utf-8", errors="replace")


def _proxy_mapping(proxy_url: str | None) -> dict[str, str] | None:
    if not proxy_url:
        return None
    return {"http": proxy_url, "https": proxy_url}


def _bootstrap_visitor_token(*, proxies: dict[str, str] | None) -> str | None:
    response = curl_requests.get(
        "https://www.upwork.com/",
        impersonate="chrome",
        proxies=cast(Any, proxies),
        timeout=30,
    )
    text = _read_response_text(response)
    classify_http_status(response.status_code, text)
    token = response.cookies.get("visitor_gql_token")
    if isinstance(token, str) and token:
        return token
    return None


def _decode_graphql_response(response: curl_requests.Response) -> dict[str, Any]:
    text = _read_response_text(response)
    classify_http_status(response.status_code, text)
    try:
        decoded = cast(Any, response.json())  # type: ignore[no-untyped-call]
    except json.JSONDecodeError as exc:
        raise UpstreamSchemaOrTemporaryError("upstream returned non-JSON response") from exc
    if not isinstance(decoded, dict):
        raise UpstreamSchemaOrTemporaryError("upstream GraphQL response is not an object")
    return decoded


def collect_live(
    query: str | None, *, max_pages: int = 1, page_size: int = 50
) -> list[dict[str, Any]]:
    require_live_enabled()
    credentials = load_credential_references()
    proxies = _proxy_mapping(credentials.proxy_url.value if credentials.proxy_url else None)
    headers = dict(HEADERS)

    try:
        visitor_token = _bootstrap_visitor_token(proxies=proxies)
        if not visitor_token:
            raise UpstreamSchemaOrTemporaryError("upstream visitor token bootstrap failed")
        headers["Authorization"] = f"Bearer {visitor_token}"
        all_results: list[dict[str, Any]] = []
        for page in range(max_pages):
            if page > 0:
                time.sleep(random.uniform(1.5, 3.0))
            payload = build_request_payload(query, offset=page * page_size, count=page_size)
            response = curl_requests.post(
                ENDPOINT,
                headers=headers,
                json=payload,
                impersonate="chrome",
                proxies=cast(Any, proxies),
                timeout=30,
            )
            all_results.append(_decode_graphql_response(response))
        return all_results
    except CollectorError:
        raise
    except curl_requests.exceptions.RequestException as exc:
        raise UpstreamSchemaOrTemporaryError(redact(f"upstream network failure: {exc}")) from exc
