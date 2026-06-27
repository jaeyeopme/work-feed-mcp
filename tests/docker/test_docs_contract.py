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
    quick_start = _section("Quick start")
    configuration = _section("Configuration")
    operate = _section("Operate the runtime")
    readme = _readme()

    for expected in [
        "docker compose up -d --build",
        "docker compose ps",
        "jobs_recent",
        "limit: 5",
    ]:
        assert expected in quick_start

    for expected in [
        "docker compose logs -f",
        "docker compose restart",
        "docker compose down",
        "docker compose exec work-feed-worker work-feed scheduler-status",
    ]:
        assert expected in operate

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
        assert variable in configuration

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
        "not affiliated with, endorsed by, or sponsored by Upwork Inc.",
        "Operators are responsible for using only sources they are authorized",
        "credentials, cookies, proxy bypasses",
        "raw upstream private payloads",
        "proposal/message generation",
        "auto-apply",
        "http://127.0.0.1:8000/mcp",
        "not_ready",
        "db_missing",
        "schema_missing",
        "unsupported_schema",
    ]:
        assert expected in section

    for forbidden in [
        "make",
        "uv run",
        "docs/",
        "Claude Code",
        "Codex",
        "/tmp/",
    ]:
        assert forbidden.lower() not in section.lower()
    assert "```mermaid" in readme
    assert "sequenceDiagram" in readme
    assert not KOREAN_RE.search(section)


def test_readme_whole_document_boundaries() -> None:
    readme = _readme()
    assert not KOREAN_RE.search(readme)
    assert "make" not in readme
    assert "## CI/CD" not in readme
    assert "proxy acquisition" not in readme.lower()
    assert "access-control bypass" not in readme.lower()
    assert "cookie/session setup" not in readme.lower()
    assert "auto-apply instructions" not in readme.lower()
    assert "proposal instructions" not in readme.lower()


def test_core_docs_track_docker_mcp_runtime() -> None:
    docs = {
        "AGENTS.md": Path("AGENTS.md").read_text(),
        "docs/PRD.md": Path("docs/PRD.md").read_text(),
        "docs/ARCHITECTURE.md": Path("docs/ARCHITECTURE.md").read_text(),
        "docs/TRD.md": Path("docs/TRD.md").read_text(),
    }

    for path, text in docs.items():
        assert "MCP" in text, path
        assert "CLI-first" not in text, path
        assert "app-native scheduler daemon" not in text, path

    assert "Docker/MCP-first" in docs["AGENTS.md"]
    assert "Docker/MCP-first" in docs["docs/PRD.md"]
    assert "http://127.0.0.1:8000/mcp" in docs["docs/PRD.md"]
    assert "docker compose up -d --build" in docs["docs/PRD.md"]
    assert "docker compose ps" in docs["docs/PRD.md"]


def test_architecture_documents_db_readiness_policy() -> None:
    architecture = Path("docs/ARCHITECTURE.md").read_text()

    assert "## Runtime Components" in architecture
    assert "MCP read" in architecture
    assert "MCP control" in architecture
    assert "scheduler-status" in architecture
    assert "current exception" in architecture


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


def test_project_local_agent_skill_is_not_part_of_public_surface() -> None:
    readme = _readme()
    prd = Path("docs/PRD.md").read_text()
    adr = Path("docs/adr/0005-keep-ranking-outside-core-data-engine.md").read_text()
    architecture = Path("docs/ARCHITECTURE.md").read_text()

    assert not Path("skills").exists()
    assert "skills/work-feed-jobs" not in readme
    assert "## Agent skill for collected jobs" not in readme
    assert "## Codex skill for collected jobs" not in readme
    assert "skills/work-feed-jobs" not in prd
    assert "repository-local" not in adr
    assert "skills/work-feed-jobs" not in adr
    assert "MCP" in architecture
