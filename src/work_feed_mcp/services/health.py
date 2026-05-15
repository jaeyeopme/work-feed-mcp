"""Container/local health checks for collector runtime roles."""

from __future__ import annotations

from pathlib import Path
from typing import Any, Literal
from urllib.error import HTTPError
from urllib.request import Request, urlopen

from work_feed_mcp.services.collector_control import NotReadyError, ensure_ready_read

HealthRole = Literal["worker", "mcp", "all"]


def health_check(
    db_path: str,
    *,
    role: HealthRole = "all",
    http_url: str | None = None,
    http_timeout: float = 2.0,
) -> dict[str, Any]:
    """Return JSON-safe runtime readiness for Docker healthchecks and humans."""

    checks: dict[str, Any] = {
        "db_path": db_path,
        "db_exists": Path(db_path).exists(),
        "schema": "unknown",
        "config": "unknown",
    }
    try:
        connection = ensure_ready_read(db_path)
    except NotReadyError as exc:
        checks["schema"] = exc.reason
        checks["config"] = "unknown"
        return {
            "ok": False,
            "role": role,
            "status": "not_ready",
            "reason": exc.reason,
            "checks": checks,
        }

    try:
        config_count = connection.execute(
            "SELECT COUNT(*) AS count FROM collector_config"
        ).fetchone()
        checks["schema"] = "ready"
        checks["config"] = "ready" if int(config_count["count"]) > 0 else "empty"
    finally:
        connection.close()

    if checks["config"] != "ready":
        return {
            "ok": False,
            "role": role,
            "status": "not_ready",
            "reason": "config_empty",
            "checks": checks,
        }

    if role == "mcp" and http_url:
        http_check = _http_reachability(http_url, timeout=http_timeout)
        checks.update(http_check)
        if not http_check["http_reachable"]:
            return {
                "ok": False,
                "role": role,
                "status": "not_ready",
                "reason": "http_unreachable",
                "checks": checks,
            }

    return {
        "ok": True,
        "role": role,
        "status": "ready",
        "checks": checks,
    }


def _http_reachability(url: str, *, timeout: float) -> dict[str, Any]:
    request = Request(url, method="GET")
    try:
        with urlopen(request, timeout=timeout) as response:  # noqa: S310 - local health URL
            return {
                "http_url": url,
                "http_reachable": True,
                "http_status": response.status,
            }
    except HTTPError as exc:
        return {
            "http_url": url,
            "http_reachable": True,
            "http_status": exc.code,
        }
    except OSError as exc:
        return {
            "http_url": url,
            "http_reachable": False,
            "http_error": str(exc),
        }
