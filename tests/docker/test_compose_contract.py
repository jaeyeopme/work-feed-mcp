from __future__ import annotations

import os
import pathlib
import subprocess


def test_compose_contract() -> None:
    compose = pathlib.Path("compose.yaml").read_text()
    assert "work-feed-worker:" in compose
    assert "work-feed-mcp:" in compose
    assert 'WORK_FEED_LIVE: "${WORK_FEED_LIVE:-1}"' in compose
    assert 'WORK_FEED_MAX_PAGES: "${WORK_FEED_MAX_PAGES:-5}"' in compose
    assert 'WORK_FEED_MCP_PATH: "${WORK_FEED_MCP_PATH:-/mcp}"' in compose
    assert 'WORK_FEED_MCP_TRANSPORT: "streamable-http"' in compose
    assert "127.0.0.1:${WORK_FEED_MCP_PORT:-8000}" in compose
    assert compose.count("work-feed-data:/data") == 2
    assert '"work-feed", "health", "--role", "worker"' in compose
    assert "work-feed health --role mcp" in compose
    assert "--http-url http://127.0.0.1:" in compose
    assert "$${WORK_FEED_MCP_PATH:-/mcp}" in compose
    assert "condition: service_healthy" in compose


def test_compose_uses_env_overrides() -> None:
    env = os.environ.copy()
    env.update(
        {
            "WORK_FEED_INTERVAL_SECONDS": "1800",
            "WORK_FEED_MAX_PAGES": "3",
            "WORK_FEED_PAGE_SIZE": "25",
            "WORK_FEED_QUERIES": "python,scraping",
            "WORK_FEED_MCP_PORT": "8765",
            "WORK_FEED_MCP_PATH": "/custom-mcp",
        }
    )
    rendered = subprocess.check_output(["docker", "compose", "config"], text=True, env=env)
    assert 'WORK_FEED_INTERVAL_SECONDS: "1800"' in rendered
    assert 'WORK_FEED_MAX_PAGES: "3"' in rendered
    assert 'WORK_FEED_PAGE_SIZE: "25"' in rendered
    assert "WORK_FEED_QUERIES: python,scraping" in rendered
    assert "WORK_FEED_MCP_PATH: /custom-mcp" in rendered
    assert "WORK_FEED_MCP_TRANSPORT: streamable-http" in rendered
    assert "host_ip: 127.0.0.1" in rendered
    assert "target: 8765" in rendered
    assert 'published: "8765"' in rendered


def test_dockerfile_uses_locked_uv_runtime() -> None:
    dockerfile = pathlib.Path("Dockerfile").read_text()
    assert "FROM python:3.13-slim" in dockerfile
    assert "pip install --no-cache-dir uv" in dockerfile
    assert "COPY pyproject.toml uv.lock README.md ./" in dockerfile
    assert "uv sync --frozen --no-dev --compile-bytecode" in dockerfile
    assert 'PATH="/app/.venv/bin:$PATH"' in dockerfile
    assert "pip install --no-cache-dir ." not in dockerfile


def test_dockerignore_excludes_local_runtime_artifacts() -> None:
    dockerignore = pathlib.Path(".dockerignore").read_text().splitlines()
    for pattern in [".venv", ".mypy_cache", ".pytest_cache", ".ruff_cache", "skills"]:
        assert pattern in dockerignore
    for pattern in ["*.sqlite", "*.db", "__pycache__", "*.py[cod]", "data"]:
        assert pattern in dockerignore


def test_cli_exposes_mcp_protocol_smoke() -> None:
    cli = pathlib.Path("src/work_feed_mcp/cli/__main__.py").read_text()
    smoke = pathlib.Path("src/work_feed_mcp/cli/mcp_smoke.py").read_text()
    assert 'subcommands.add_parser("mcp-smoke", add_help=False)' in cli
    assert "streamable_http_client" in smoke
    assert "jobs_recent" in smoke
