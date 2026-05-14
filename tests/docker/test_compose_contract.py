from __future__ import annotations

import os
import pathlib
import subprocess


def test_compose_contract() -> None:
    compose = pathlib.Path("compose.yaml").read_text()
    assert "collector-worker:" in compose
    assert "upwork-collector-mcp:" in compose
    assert 'UPWORK_COLLECTOR_LIVE: "${UPWORK_COLLECTOR_LIVE:-1}"' in compose
    assert 'UPWORK_COLLECTOR_MAX_PAGES: "${UPWORK_COLLECTOR_MAX_PAGES:-5}"' in compose
    assert (
        'UPWORK_COLLECTOR_MCP_TRANSPORT: "${UPWORK_COLLECTOR_MCP_TRANSPORT:-streamable-http}"'
        in compose
    )
    assert "127.0.0.1:${UPWORK_COLLECTOR_MCP_PORT:-8000}" in compose
    assert compose.count("upwork-data:/data") == 2


def test_compose_uses_env_overrides() -> None:
    env = os.environ.copy()
    env.update(
        {
            "UPWORK_COLLECTOR_INTERVAL_SECONDS": "1800",
            "UPWORK_COLLECTOR_MAX_PAGES": "3",
            "UPWORK_COLLECTOR_PAGE_SIZE": "25",
            "UPWORK_COLLECTOR_QUERIES": "python,scraping",
            "UPWORK_COLLECTOR_MCP_PORT": "8765",
        }
    )
    rendered = subprocess.check_output(["docker", "compose", "config"], text=True, env=env)
    assert 'UPWORK_COLLECTOR_INTERVAL_SECONDS: "1800"' in rendered
    assert 'UPWORK_COLLECTOR_MAX_PAGES: "3"' in rendered
    assert 'UPWORK_COLLECTOR_PAGE_SIZE: "25"' in rendered
    assert "UPWORK_COLLECTOR_QUERIES: python,scraping" in rendered
    assert "host_ip: 127.0.0.1" in rendered
    assert "target: 8765" in rendered
    assert 'published: "8765"' in rendered
