from __future__ import annotations

from pathlib import Path

from work_feed_mcp.runtime.config import DEFAULT_MCP_PATH, load_runtime_settings


def test_worker_defaults_are_container_defaults() -> None:
    settings = load_runtime_settings({})
    assert settings.interval_seconds == 3600
    assert settings.max_pages == 5
    assert settings.page_size == 50
    assert settings.queries is None
    assert settings.live is True
    assert DEFAULT_MCP_PATH == "/mcp"
    assert settings.mcp_path == "/mcp"
    assert settings.mcp_transport == "streamable-http"


def test_mcp_path_env_override() -> None:
    settings = load_runtime_settings({"WORK_FEED_MCP_PATH": "/custom-mcp"})
    assert settings.mcp_path == "/custom-mcp"


def test_mcp_transport_stays_internal_default() -> None:
    readme = Path("README.md").read_text()
    env_example = Path(".env.example").read_text()
    assert "WORK_FEED_MCP_TRANSPORT" not in readme
    assert "WORK_FEED_MCP_TRANSPORT" not in env_example
    assert load_runtime_settings({}).mcp_transport == "streamable-http"
