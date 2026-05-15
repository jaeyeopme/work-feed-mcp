from __future__ import annotations

import pathlib


def test_readme_links_mcp_client_setup_once_in_quickstart() -> None:
    readme = pathlib.Path("README.md").read_text()
    quickstart = readme.split("## 설치 / 준비", maxsplit=1)[0]
    assert quickstart.count("docs/mcp-client-setup.md") == 1


def test_mcp_client_setup_contract() -> None:
    docs = pathlib.Path("docs/mcp-client-setup.md").read_text()
    assert "http://127.0.0.1:8000/mcp" in docs
    assert "Streamable HTTP MCP" in docs
    assert "not a REST API" in docs
    assert "exact config syntax varies by MCP client and version" in docs
    assert "README Docker + MCP quickstart tool list" in docs
    assert "Docker health checks" in docs
    assert "do **not** run a full MCP protocol" in docs
    forbidden = ["proxy acquisition", "bypass", "cookie", "session"]
    assert not any(term in docs.lower() for term in forbidden)
    assert "not an auto-apply" in docs
