from __future__ import annotations

from work_feed_mcp.mcp_server.server import (
    ConfigUpdate,
    build_server,
    configure_streamable_http_settings,
)
from work_feed_mcp.runtime.config import RuntimeSettings


def test_streamable_http_path_is_explicitly_configured() -> None:
    settings = RuntimeSettings(mcp_host="0.0.0.0", mcp_port=8765, mcp_path="/custom-mcp")
    server = build_server(settings)

    configure_streamable_http_settings(server, settings)

    assert server.settings.host == "0.0.0.0"
    assert server.settings.port == 8765
    assert server.settings.streamable_http_path == "/custom-mcp"


def test_config_update_schema_lists_allowed_update_fields() -> None:
    server = build_server(RuntimeSettings())
    tool = server._tool_manager.get_tool("config_update")

    assert tool is not None
    schema = tool.parameters
    update_schema = schema["$defs"]["ConfigUpdate"]
    assert update_schema["additionalProperties"] is False
    assert set(update_schema["properties"]) == {
        "interval_seconds",
        "queries",
        "max_pages",
        "page_size",
        "paused",
    }


def test_config_update_model_drops_omitted_values() -> None:
    update = ConfigUpdate(page_size=25)

    assert update.to_update_dict() == {"page_size": 25}
