"""FastMCP server for the Upwork collector."""

from __future__ import annotations

from typing import Any

from mcp.server.fastmcp import FastMCP

from upwork_app.mcp_server import tools
from upwork_app.runtime.config import RuntimeSettings, load_runtime_settings


def build_server(settings: RuntimeSettings | None = None) -> FastMCP:
    resolved = settings or load_runtime_settings()
    mcp = FastMCP("upwork-collector")

    @mcp.tool()
    def jobs_recent(limit: int = 20) -> dict[str, Any]:
        """List recently collected Upwork jobs."""

        return tools.jobs_recent(limit=limit, settings=resolved)

    @mcp.tool()
    def jobs_search(
        title: str | None = None, skill: str | None = None, limit: int = 20
    ) -> dict[str, Any]:
        """Search collected jobs by title keyword and/or normalized skill."""

        return tools.jobs_search(title=title, skill=skill, limit=limit, settings=resolved)

    @mcp.tool()
    def jobs_get(job_id: str) -> dict[str, Any]:
        """Return one collected job by job_id."""

        return tools.jobs_get(job_id=job_id, settings=resolved)

    @mcp.tool()
    def runs_recent(limit: int = 5) -> dict[str, Any]:
        """Return recent collector runs and query results."""

        return tools.runs_recent(limit=limit, settings=resolved)

    @mcp.tool()
    def collector_status() -> dict[str, Any]:
        """Return collector status, effective config, and recent commands."""

        return tools.collector_status(settings=resolved)

    @mcp.tool()
    def config_get() -> dict[str, Any]:
        """Return current collector runtime config."""

        return tools.config_get(settings=resolved)

    @mcp.tool()
    def config_update(updates: dict[str, Any]) -> dict[str, Any]:
        """Update mutable collector runtime config."""

        return tools.config_update(updates=updates, settings=resolved)

    @mcp.tool()
    def collector_run_once() -> dict[str, Any]:
        """Queue one manual collector run."""

        return tools.collector_run_once(settings=resolved)

    @mcp.tool()
    def collector_pause() -> dict[str, Any]:
        """Queue collector pause."""

        return tools.collector_pause(settings=resolved)

    @mcp.tool()
    def collector_resume() -> dict[str, Any]:
        """Queue collector resume."""

        return tools.collector_resume(settings=resolved)

    @mcp.tool()
    def collector_command_status(command_id: str) -> dict[str, Any]:
        """Return one collector command status."""

        return tools.collector_command_status(command_id=command_id, settings=resolved)

    return mcp


def configure_streamable_http_settings(server: FastMCP, settings: RuntimeSettings) -> None:
    server.settings.host = settings.mcp_host
    server.settings.port = settings.mcp_port
    server.settings.streamable_http_path = settings.mcp_path


def run_server(settings: RuntimeSettings | None = None) -> None:
    resolved = settings or load_runtime_settings()
    server = build_server(resolved)
    if resolved.mcp_transport == "stdio":
        server.run(transport="stdio")
    else:
        configure_streamable_http_settings(server, resolved)
        server.run(transport="streamable-http")
