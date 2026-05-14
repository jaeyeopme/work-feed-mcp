"""Runtime configuration for Docker worker and MCP entrypoints."""

from __future__ import annotations

import os
from collections.abc import Mapping
from dataclasses import dataclass
from typing import Any

DEFAULT_DB_PATH = "/data/upwork.sqlite"
DEFAULT_INTERVAL_SECONDS = 3600
DEFAULT_MAX_PAGES = 5
DEFAULT_PAGE_SIZE = 50
DEFAULT_MCP_HOST = "127.0.0.1"
DEFAULT_MCP_PORT = 8000


@dataclass(frozen=True, slots=True)
class RuntimeSettings:
    db_path: str = DEFAULT_DB_PATH
    interval_seconds: int = DEFAULT_INTERVAL_SECONDS
    queries: tuple[str, ...] | None = None
    max_pages: int = DEFAULT_MAX_PAGES
    page_size: int = DEFAULT_PAGE_SIZE
    paused: bool = False
    live: bool = True
    mcp_host: str = DEFAULT_MCP_HOST
    mcp_port: int = DEFAULT_MCP_PORT
    mcp_transport: str = "streamable-http"
    log_level: str = "INFO"
    fixture_path: str | None = None

    def persisted_defaults(self) -> dict[str, Any]:
        return {
            "interval_seconds": self.interval_seconds,
            "queries": list(self.queries) if self.queries is not None else [],
            "max_pages": self.max_pages,
            "page_size": self.page_size,
            "paused": self.paused,
        }


def load_runtime_settings(env: Mapping[str, str] | None = None) -> RuntimeSettings:
    source = os.environ if env is None else env
    return RuntimeSettings(
        db_path=source.get("UPWORK_COLLECTOR_DB", DEFAULT_DB_PATH),
        interval_seconds=_int(
            source.get("UPWORK_COLLECTOR_INTERVAL_SECONDS"), DEFAULT_INTERVAL_SECONDS
        ),
        queries=_queries(source.get("UPWORK_COLLECTOR_QUERIES")),
        max_pages=_int(source.get("UPWORK_COLLECTOR_MAX_PAGES"), DEFAULT_MAX_PAGES),
        page_size=_int(source.get("UPWORK_COLLECTOR_PAGE_SIZE"), DEFAULT_PAGE_SIZE),
        paused=_bool(source.get("UPWORK_COLLECTOR_PAUSED"), False),
        live=source.get("UPWORK_COLLECTOR_LIVE", "1") == "1",
        mcp_host=source.get("UPWORK_COLLECTOR_MCP_HOST", DEFAULT_MCP_HOST),
        mcp_port=_int(source.get("UPWORK_COLLECTOR_MCP_PORT"), DEFAULT_MCP_PORT),
        mcp_transport=source.get("UPWORK_COLLECTOR_MCP_TRANSPORT", "streamable-http"),
        log_level=source.get("UPWORK_COLLECTOR_LOG_LEVEL", "INFO"),
        fixture_path=source.get("UPWORK_COLLECTOR_FIXTURE") or None,
    )


def _int(value: str | None, default: int) -> int:
    if value is None or value == "":
        return default
    parsed = int(value)
    if parsed < 1:
        raise ValueError("runtime integer settings must be >= 1")
    return parsed


def _bool(value: str | None, default: bool) -> bool:
    if value is None or value == "":
        return default
    return value.lower() in {"1", "true", "yes", "on"}


def _queries(value: str | None) -> tuple[str, ...] | None:
    if value is None or not value.strip():
        return None
    parsed = tuple(part.strip() for part in value.split(",") if part.strip())
    return parsed or None
