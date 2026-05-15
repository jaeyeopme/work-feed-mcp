from __future__ import annotations

from upwork_app.mcp_server.server import build_server, configure_streamable_http_settings
from upwork_app.runtime.config import RuntimeSettings


def test_streamable_http_path_is_explicitly_configured() -> None:
    settings = RuntimeSettings(mcp_host="0.0.0.0", mcp_port=8765, mcp_path="/custom-mcp")
    server = build_server(settings)

    configure_streamable_http_settings(server, settings)

    assert server.settings.host == "0.0.0.0"
    assert server.settings.port == 8765
    assert server.settings.streamable_http_path == "/custom-mcp"
