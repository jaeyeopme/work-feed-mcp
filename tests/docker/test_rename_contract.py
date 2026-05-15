from __future__ import annotations

import tomllib
from pathlib import Path

SCAN_PATHS = [
    Path("README.md"),
    Path("docs"),
    Path("pyproject.toml"),
    Path("uv.lock"),
    Path("Dockerfile"),
    Path(".env.example"),
    Path("compose.yaml"),
    Path("Makefile"),
    Path("src"),
    Path("tests"),
    Path("AGENTS.md"),
]


def _tracked_text_files(root: Path) -> list[Path]:
    if root.is_file():
        return [root]
    return [path for path in root.rglob("*") if path.is_file() and "__pycache__" not in path.parts]


def test_package_module_and_cli_names() -> None:
    pyproject = tomllib.loads(Path("pyproject.toml").read_text())
    assert pyproject["project"]["name"] == "work-feed-mcp"
    assert pyproject["project"]["scripts"] == {"work-feed": "work_feed_mcp.cli.__main__:main"}
    assert pyproject["tool"]["mypy"]["packages"] == ["work_feed_mcp"]
    assert Path("src/work_feed_mcp").is_dir()
    assert not Path("src/" + "upwork" + "_app").exists()


def test_docker_compose_runtime_names() -> None:
    compose = Path("compose.yaml").read_text()
    assert "work-feed-mcp:local" in compose
    assert "work-feed-worker:" in compose
    assert "work-feed-mcp:" in compose
    assert "work-feed-data:" in compose
    assert '["work-feed", "worker"]' in compose
    assert '["work-feed", "mcp-server"]' in compose
    assert '["CMD", "work-feed", "health"' in compose


def test_runtime_env_names() -> None:
    env = Path(".env.example").read_text()
    runtime_config = Path("src/work_feed_mcp/runtime/config.py").read_text()
    credentials = Path("src/work_feed_mcp/integrations/upwork/credentials.py").read_text()
    for name in [
        "WORK_FEED_DB",
        "WORK_FEED_LIVE",
        "WORK_FEED_INTERVAL_SECONDS",
        "WORK_FEED_MAX_PAGES",
        "WORK_FEED_PAGE_SIZE",
        "WORK_FEED_QUERIES",
        "WORK_FEED_PAUSED",
        "WORK_FEED_FIXTURE",
        "WORK_FEED_PROXY_URL",
        "WORK_FEED_MCP_HOST",
        "WORK_FEED_MCP_PORT",
        "WORK_FEED_MCP_PATH",
        "WORK_FEED_MCP_TRANSPORT",
    ]:
        assert name in env + runtime_config + credentials


def test_mcp_server_name_is_work_feed() -> None:
    server = Path("src/work_feed_mcp/mcp_server/server.py").read_text()
    readme = Path("README.md").read_text()
    assert 'FastMCP("work-feed")' in server
    assert '"work-feed"' in readme
    assert "docs/mcp-client-setup.md" not in readme
    assert not Path("docs/mcp-client-setup.md").exists()


def test_allowlisted_stale_name_contract() -> None:
    banned = [
        "upwork" + "-app",
        "upwork" + "_app",
        "upwork" + "-collector",
        "UPWORK" + "_COLLECTOR",
        "UPWORK" + "_APP_DB",
        "live is intentionally not MCP" + "-mutable",
    ]
    allowed_fragments = [
        "Upwork",
        'source="upwork"',
        "source='upwork'",
        "'upwork'",
        '"upwork"',
        "integrations/upwork",
        "www.upwork.com",
        "X-Upwork-Accept-Language",
        "test_rename_contract.py",
    ]
    violations: list[str] = []
    for root in SCAN_PATHS:
        if not root.exists():
            continue
        for path in _tracked_text_files(root):
            try:
                text = path.read_text()
            except UnicodeDecodeError:
                continue
            for line_no, line in enumerate(text.splitlines(), start=1):
                for token in banned:
                    if token not in line:
                        continue
                    if any(fragment in line for fragment in allowed_fragments):
                        continue
                    violations.append(f"{path}:{line_no}: {token}")
    assert not violations


def test_readme_uses_mermaid_sequence_diagram() -> None:
    readme = Path("README.md").read_text()
    assert "```mermaid" in readme
    assert "sequenceDiagram" in readme
    assert "work-feed-worker" in readme
    assert "work-feed-mcp" in readme
    assert "SQLite volume" in readme
    assert not Path("docs/architecture.d2").exists()
    assert not Path("docs/architecture.svg").exists()
