"""Live HTTP transport kept behind a narrow boundary."""

from __future__ import annotations

import json
import os
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

USER_AGENT = "Mozilla/5.0 (Macintosh; Intel Mac OS X) AppleWebKit/537.36 Chrome Safari"


def require_live_enabled(env: dict[str, str] | None = None) -> None:
    source = os.environ if env is None else env
    if source.get("UPWORK_COLLECTOR_LIVE") != "1":
        raise CredentialRequiredError("live collection requires UPWORK_COLLECTOR_LIVE=1")


def classify_http_status(status: int, body: str = "") -> None:
    lowered = body.lower()
    if status in {401, 403} or "access denied" in lowered or "forbidden" in lowered:
        raise UpstreamBlockedError("upstream blocked or denied the request")
    if status == 429 or "rate limit" in lowered or "throttle" in lowered:
        raise RateLimitedError("upstream rate limited the request")
    if status >= 500:
        raise UpstreamSchemaOrTemporaryError("upstream temporary server failure")


def collect_live(
    query: str | None, *, max_pages: int = 1, page_size: int = 10
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
    headers = {"User-Agent": USER_AGENT, "Accept": "application/json"}
    cookie_values = [
        secret.value for secret in (credentials.cookie, credentials.session) if secret is not None
    ]
    if cookie_values:
        headers["Cookie"] = "; ".join(cookie_values)

    try:
        opener.open(urllib.request.Request("https://www.upwork.com/", headers=headers), timeout=20)
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
