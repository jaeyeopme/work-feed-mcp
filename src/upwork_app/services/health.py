"""Container/local health checks for collector runtime roles."""

from __future__ import annotations

from pathlib import Path
from typing import Any, Literal

from upwork_app.services.collector_control import NotReadyError, ensure_ready_read

HealthRole = Literal["worker", "mcp", "all"]


def health_check(db_path: str, *, role: HealthRole = "all") -> dict[str, Any]:
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
        ok = checks["config"] == "ready"
        return {
            "ok": ok,
            "role": role,
            "status": "ready" if ok else "not_ready",
            "checks": checks,
        }
    finally:
        connection.close()
