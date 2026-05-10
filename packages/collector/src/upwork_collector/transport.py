"""Compatibility shim for live Upwork transport."""

from upwork_app.integrations.upwork.transport import (
    USER_AGENT,
    _extract_visitor_token,
    classify_http_status,
    collect_live,
    require_live_enabled,
)

__all__ = [
    "USER_AGENT",
    "_extract_visitor_token",
    "classify_http_status",
    "collect_live",
    "require_live_enabled",
]
