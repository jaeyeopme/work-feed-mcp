from __future__ import annotations

import pytest

from work_feed_mcp.integrations.upwork.errors import (
    RateLimitedError,
    UpstreamBlockedError,
    UpstreamSchemaOrTemporaryError,
)
from work_feed_mcp.services.retry import RetryExhausted, collect_with_retry


def _constant_jitter(low: float, high: float) -> float:
    return low


def test_temporary_errors_retry_three_attempts_without_real_sleep() -> None:
    calls = 0
    delays: list[float] = []

    def operation() -> str:
        nonlocal calls
        calls += 1
        if calls < 3:
            raise UpstreamSchemaOrTemporaryError("temporary")
        return "ok"

    result, attempts = collect_with_retry(
        operation,
        sleep=delays.append,
        jitter=_constant_jitter,
    )

    assert result == "ok"
    assert attempts == 3
    assert delays == [24.0, 48.0]


def test_rate_limit_gets_one_delayed_retry() -> None:
    calls = 0
    delays: list[float] = []

    def operation() -> str:
        nonlocal calls
        calls += 1
        raise RateLimitedError("rate limit")

    with pytest.raises(RetryExhausted) as raised:
        collect_with_retry(operation, sleep=delays.append, jitter=_constant_jitter)

    assert calls == 2
    assert raised.value.attempts == 2
    assert delays == [120.0]


def test_blocked_errors_do_not_retry() -> None:
    calls = 0

    def operation() -> str:
        nonlocal calls
        calls += 1
        raise UpstreamBlockedError("blocked")

    with pytest.raises(RetryExhausted) as raised:
        collect_with_retry(operation, sleep=lambda _: None, jitter=_constant_jitter)

    assert calls == 1
    assert raised.value.attempts == 1
