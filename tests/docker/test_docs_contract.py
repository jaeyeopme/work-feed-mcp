from __future__ import annotations

import re
from pathlib import Path


def _readme() -> str:
    return Path("README.md").read_text()


def _primary_user_section() -> str:
    readme = _readme()
    match = re.search(r"^## User guide\n(?P<section>.*?)(?=^## )", readme, flags=re.M | re.S)
    assert match is not None
    return match.group("section")


def test_readme_primary_user_section_contract() -> None:
    section = _primary_user_section()
    assert "docker compose up -d" in section
    assert "docker compose ps" in section
    assert "http://127.0.0.1:8000/mcp" in section
    assert section.count("docs/mcp-client-setup.md") == 1

    for tool in [
        "jobs_recent",
        "jobs_search",
        "jobs_get",
        "runs_recent",
        "collector_status",
        "config_get",
        "config_update",
        "collector_run_once",
        "collector_pause",
        "collector_resume",
        "collector_command_status",
    ]:
        assert tool in section

    for expected in [
        "normal user",
        "Not a REST API",
        "Not a recommendation engine",
        "Not auto-apply",
        "Not proposal/message generation",
        "enqueue-only",
        "collector_command_status",
        "not_ready",
        "db_missing",
        "schema_missing",
        "Config precedence",
    ]:
        assert expected in section

    forbidden = [
        "fixture",
        "mock",
        "make smoke",
        "make e2e-smoke",
        "make quality",
        "CI/CD",
        "GitHub Actions",
        "upwork-app health",
        "/tmp/upwork-worker-smoke.sqlite",
        "/tmp/",
    ]
    lowered = section.lower()
    assert not any(term.lower() in lowered for term in forbidden)


def test_readme_whole_document_boundaries() -> None:
    readme = _readme()
    assert "## CI/CD" not in readme
    assert "proxy acquisition" not in readme.lower()
    assert "access-control bypass" not in readme.lower()
    assert "cookie/session setup" not in readme.lower()
    assert "auto-apply instructions" not in readme.lower()
    assert "proposal instructions" not in readme.lower()


def test_mcp_client_setup_contract() -> None:
    docs = Path("docs/mcp-client-setup.md").read_text()
    assert "http://127.0.0.1:8000/mcp" in docs
    assert "Streamable HTTP MCP" in docs
    assert "not a REST API" in docs
    assert "Exact config syntax varies by MCP client and version" in docs
    assert "README User guide tool list" in docs
    assert "Docker health checks" in docs
    assert "do **not** run a full MCP protocol" in docs
    forbidden = [
        "fixture",
        "mock",
        "live-smoke",
        "make live-smoke",
        "CI/CD",
        "proxy acquisition",
        "bypass",
        "cookie/session",
        "auto-apply instructions",
        "proposal instructions",
    ]
    lowered = docs.lower()
    assert not any(term.lower() in lowered for term in forbidden)
    assert "not an auto-apply" in docs
