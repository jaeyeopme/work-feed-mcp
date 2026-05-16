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
        r"^# work-feed-mcp\n(?P<section>.*?)(?=^## Developer reference)", readme, flags=re.M | re.S
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
    assert "# work-feed-mcp" in _readme()
    assert "```mermaid" in _readme()
    assert "sequenceDiagram" in _readme()
    assert "not affiliated with, endorsed by, or sponsored by Upwork Inc." in _readme()
    assert "http://127.0.0.1:8000/mcp" in section
    assert "docs/mcp-client-setup.md" not in section
    assert "## Connect an MCP client" in _readme()
    assert "### Claude Code" in section
    assert "claude mcp add --transport http work-feed http://127.0.0.1:8000/mcp" in section
    assert '"type": "http"' in section
    assert "### Codex" in section
    assert "codex mcp add work-feed --url http://127.0.0.1:8000/mcp" in section
    assert "[mcp_servers.work-feed]" in section
    assert "Codex infers streamable HTTP from `url`" in section
    assert "jobs_recent" in section
    assert "limit: 5" in section
    assert "recreate the runtime" in section
    assert "Docker health checks" in section
    assert "do **not** run a full MCP protocol" in section
    assert "docker compose up -d" not in section
    assert "uv run" not in section
    assert not KOREAN_RE.search(section)

    for variable in [
        "WORK_FEED_LIVE",
        "WORK_FEED_INTERVAL_SECONDS",
        "WORK_FEED_MAX_PAGES",
        "WORK_FEED_PAGE_SIZE",
        "WORK_FEED_QUERIES",
        "WORK_FEED_LOG_LEVEL",
        "WORK_FEED_MCP_HOST",
        "WORK_FEED_MCP_PORT",
        "WORK_FEED_MCP_PATH",
        "WORK_FEED_DB",
    ]:
        assert variable in section
    assert "WORK_FEED_MCP_TRANSPORT" not in section

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
        "unsupported_schema",
        "upgrade work-feed or migrate the database",
        "Config precedence",
        "Live collection mode is set by Docker/.env at startup",
        "cannot switch the runtime between live and non-live modes",
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
        "/tmp/work-feed-worker-smoke.sqlite",
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
        "deploy/systemd/work-feed.service",
        "deploy/systemd/work-feed.timer",
        "docs/scheduler-plan.md",
        "docs/server-install.md",
        "scripts/collect_live_once.sh",
        "src/work_feed_mcp/cli/scheduler.py",
        "src/work_feed_mcp/services/system_scheduler.py",
        "src/" + "upwork" + "_app",
    ]
    for path in removed_paths:
        assert not Path(path).exists(), path

    assert ".omx/" in Path(".gitignore").read_text()


def test_project_local_agent_skill_is_documented() -> None:
    skill = Path("skills/work-feed-jobs/SKILL.md")
    metadata = Path("skills/work-feed-jobs/agents/openai.yaml")
    assert skill.exists()
    assert metadata.exists()
    assert "work-feed-jobs" in skill.read_text()
    assert "skills/work-feed-jobs" in _readme()
    assert "## Agent skill for collected jobs" in _readme()
    assert "## Codex skill for collected jobs" not in _readme()
    assert "skills/work-feed-jobs" in Path("docs/LLM_CONTEXT.md").read_text()
    assert "skills/work-feed-jobs" in Path("docs/EXTERNAL_LLM_GUIDE.md").read_text()
