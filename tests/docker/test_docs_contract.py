from __future__ import annotations

import re
from pathlib import Path

KOREAN_RE = re.compile(r"[가-힣]")


def _readme() -> str:
    return Path("README.md").read_text()


def _section(heading: str) -> str:
    readme = _readme()
    match = re.search(
        rf"^## {re.escape(heading)}\n(?P<section>.*?)(?=^## )", readme, flags=re.M | re.S
    )
    assert match is not None
    return match.group("section")


def _normal_user_docs() -> str:
    readme = _readme()
    match = re.search(
        r"^# upwork\n(?P<section>.*?)(?=^## Developer reference)", readme, flags=re.M | re.S
    )
    assert match is not None
    return match.group("section")


def test_readme_normal_user_contract() -> None:
    section = _normal_user_docs()
    assert "make up" in section
    assert "make status" in section
    assert "make logs" in section
    assert "make restart" in section
    assert "make down" in section
    assert "http://127.0.0.1:8000/mcp" in section
    assert section.count("docs/mcp-client-setup.md") == 1
    assert "docker compose up -d" not in section
    assert "uv run" not in section
    assert not KOREAN_RE.search(section)

    for variable in [
        "UPWORK_COLLECTOR_LIVE",
        "UPWORK_COLLECTOR_INTERVAL_SECONDS",
        "UPWORK_COLLECTOR_MAX_PAGES",
        "UPWORK_COLLECTOR_PAGE_SIZE",
        "UPWORK_COLLECTOR_QUERIES",
        "UPWORK_COLLECTOR_LOG_LEVEL",
        "UPWORK_COLLECTOR_MCP_PORT",
        "UPWORK_COLLECTOR_MCP_PATH",
    ]:
        assert variable in section

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
        "/tmp/upwork-worker-smoke.sqlite",
        "/tmp/",
    ]
    lowered = section.lower()
    assert not any(term.lower() in lowered for term in forbidden)


def test_readme_whole_document_boundaries() -> None:
    readme = _readme()
    assert not KOREAN_RE.search(readme)
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
    assert "README MCP tools list" in docs
    assert "Docker health checks" in docs
    assert "do **not** run a full MCP protocol" in docs
    assert "make up" in docs
    assert "make status" in docs
    assert "docker compose up -d" not in docs
    assert not KOREAN_RE.search(docs)
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


def test_agent_context_docs_track_docker_mcp_runtime() -> None:
    docs = {
        "AGENTS.md": Path("AGENTS.md").read_text(),
        "docs/LLM_CONTEXT.md": Path("docs/LLM_CONTEXT.md").read_text(),
        "docs/EXTERNAL_LLM_GUIDE.md": Path("docs/EXTERNAL_LLM_GUIDE.md").read_text(),
    }

    for path, text in docs.items():
        assert "Docker/MCP-first" in text, path
        assert "MCP" in text, path
        assert "CLI-first" not in text, path
        assert "app-native scheduler daemon" not in text, path

    external_guide = docs["docs/EXTERNAL_LLM_GUIDE.md"]
    assert "http://127.0.0.1:8000/mcp" in external_guide
    assert "make up" in external_guide
    assert "make status" in external_guide


def test_removed_legacy_public_artifacts_stay_removed() -> None:
    removed_paths = [
        ".github/workflows/deploy-server.yml",
        "deploy/systemd/upwork-collector.service",
        "deploy/systemd/upwork-collector.timer",
        "docs/scheduler-plan.md",
        "docs/server-install.md",
        "scripts/collect_live_once.sh",
        "src/upwork_app/cli/scheduler.py",
        "src/upwork_app/services/system_scheduler.py",
    ]
    for path in removed_paths:
        assert not Path(path).exists(), path

    assert ".omx/" in Path(".gitignore").read_text()
