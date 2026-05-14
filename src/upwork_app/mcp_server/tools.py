"""MCP tool implementations for Upwork collector data and control."""

from __future__ import annotations

from typing import Any

from upwork_app.runtime.config import RuntimeSettings, load_runtime_settings
from upwork_app.services.collector_control import (
    NotReadyError,
    enqueue_runtime_command,
    get_command_status,
    get_effective_config,
    update_runtime_config,
)
from upwork_app.services.job_queries import jobs_get as query_job_get
from upwork_app.services.job_queries import jobs_recent as query_jobs_recent
from upwork_app.services.job_queries import jobs_search as query_jobs_search
from upwork_app.services.run_status import run_status


def _settings(settings: RuntimeSettings | None = None) -> RuntimeSettings:
    return settings or load_runtime_settings()


def _safe(call: Any) -> dict[str, Any]:
    try:
        result = call()
        if isinstance(result, dict):
            return result
        return {"ok": True, "result": result}
    except NotReadyError as exc:
        return exc.to_dict()
    except ValueError as exc:
        return {"ok": False, "error": "invalid_request", "message": str(exc)}


def jobs_recent(*, limit: int = 20, settings: RuntimeSettings | None = None) -> dict[str, Any]:
    resolved = _settings(settings)
    return _safe(lambda: query_jobs_recent(resolved.db_path, limit=limit))


def jobs_search(
    *,
    title: str | None = None,
    skill: str | None = None,
    limit: int = 20,
    settings: RuntimeSettings | None = None,
) -> dict[str, Any]:
    resolved = _settings(settings)
    return _safe(lambda: query_jobs_search(resolved.db_path, title=title, skill=skill, limit=limit))


def jobs_get(*, job_id: str, settings: RuntimeSettings | None = None) -> dict[str, Any]:
    resolved = _settings(settings)
    return _safe(lambda: query_job_get(resolved.db_path, job_id=job_id))


def runs_recent(*, limit: int = 5, settings: RuntimeSettings | None = None) -> dict[str, Any]:
    resolved = _settings(settings)
    return _safe(lambda: run_status(resolved.db_path, limit=limit))


def collector_status(*, settings: RuntimeSettings | None = None) -> dict[str, Any]:
    resolved = _settings(settings)
    return _safe(lambda: run_status(resolved.db_path, limit=5))


def config_get(*, settings: RuntimeSettings | None = None) -> dict[str, Any]:
    resolved = _settings(settings)
    return _safe(lambda: get_effective_config(resolved.db_path))


def config_update(
    *, updates: dict[str, Any], settings: RuntimeSettings | None = None
) -> dict[str, Any]:
    resolved = _settings(settings)
    return _safe(lambda: update_runtime_config(resolved.db_path, updates))


def collector_run_once(*, settings: RuntimeSettings | None = None) -> dict[str, Any]:
    resolved = _settings(settings)
    return _safe(lambda: enqueue_runtime_command(resolved.db_path, "run_once"))


def collector_pause(*, settings: RuntimeSettings | None = None) -> dict[str, Any]:
    resolved = _settings(settings)
    return _safe(lambda: enqueue_runtime_command(resolved.db_path, "pause"))


def collector_resume(*, settings: RuntimeSettings | None = None) -> dict[str, Any]:
    resolved = _settings(settings)
    return _safe(lambda: enqueue_runtime_command(resolved.db_path, "resume"))


def collector_command_status(
    *, command_id: str, settings: RuntimeSettings | None = None
) -> dict[str, Any]:
    resolved = _settings(settings)
    return _safe(lambda: get_command_status(resolved.db_path, command_id))
