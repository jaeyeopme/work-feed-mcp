"""Retry policy for live scheduled collection."""

from __future__ import annotations

import random
import time
from collections.abc import Callable
from dataclasses import dataclass
from typing import TypeVar

from work_feed_mcp.integrations.upwork.errors import (
    CollectorError,
    RateLimitedError,
    UpstreamBlockedError,
    UpstreamSchemaOrTemporaryError,
)

Sleep = Callable[[float], None]
Jitter = Callable[[float, float], float]
T = TypeVar("T")


@dataclass(frozen=True, slots=True)
class RetryExhausted(Exception):
    error: CollectorError
    attempts: int


def default_jitter(low: float, high: float) -> float:
    return random.uniform(low, high)


def collect_with_retry(
    operation: Callable[[], T],
    *,
    sleep: Sleep = time.sleep,
    jitter: Jitter = default_jitter,
) -> tuple[T, int]:
    """Run a live collection operation with bounded retry by typed error class."""

    attempts = 0
    while True:
        attempts += 1
        try:
            return operation(), attempts
        except UpstreamBlockedError as exc:
            raise RetryExhausted(exc, attempts) from exc
        except RateLimitedError as exc:
            if attempts >= 2:
                raise RetryExhausted(exc, attempts) from exc
            sleep(jitter(120.0, 300.0))
        except UpstreamSchemaOrTemporaryError as exc:
            if attempts >= 3:
                raise RetryExhausted(exc, attempts) from exc
            base_delay = 30.0 * (2 ** (attempts - 1))
            sleep(jitter(base_delay * 0.8, base_delay * 1.2))
