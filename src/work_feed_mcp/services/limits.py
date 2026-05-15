"""Shared validation helpers for agent-facing read limits."""

from __future__ import annotations

MAX_QUERY_LIMIT = 100


def validate_limit(limit: int) -> int:
    """Return a safe bounded limit for read APIs."""

    if not isinstance(limit, int) or isinstance(limit, bool) or limit < 1:
        raise ValueError("limit must be a positive integer")
    if limit > MAX_QUERY_LIMIT:
        raise ValueError(f"limit must be <= {MAX_QUERY_LIMIT}")
    return limit
