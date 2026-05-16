from __future__ import annotations

from pathlib import Path

ROOT_OSS_FILES = [
    "LICENSE",
    "CONTRIBUTING.md",
    "SECURITY.md",
    "CHANGELOG.md",
]

GITHUB_COMMUNITY_FILES = [
    ".github/ISSUE_TEMPLATE/bug_report.md",
    ".github/ISSUE_TEMPLATE/feature_request.md",
    ".github/pull_request_template.md",
    ".github/dependabot.yml",
]


def read(path: str) -> str:
    return Path(path).read_text()


def test_root_oss_files_exist_and_are_referenced() -> None:
    for path in ROOT_OSS_FILES:
        assert Path(path).exists(), path

    readme = read("README.md")
    agent_docs = read("docs/LLM_CONTEXT.md") + read("docs/EXTERNAL_LLM_GUIDE.md")
    for path in ["CONTRIBUTING.md", "SECURITY.md", "CHANGELOG.md"]:
        assert path in readme
        assert path in agent_docs


def test_readme_exposes_project_health_without_fake_coverage_badge() -> None:
    readme = read("README.md")

    assert "actions/workflows/ci-cd.yml/badge.svg?branch=main" in readme
    assert "actions/workflows/release.yml/badge.svg" in readme
    assert "license-MIT" in readme
    assert "make architecture" in readme
    assert "make coverage" in readme
    assert "conservative coverage gate at 80%" in readme
    assert "Codecov" not in readme
    assert "coverage.svg" not in readme


def test_python_quality_gates_are_declared() -> None:
    pyproject = read("pyproject.toml")
    makefile = read("Makefile")
    workflow = read(".github/workflows/ci-cd.yml")

    assert "pytest-cov>=7.1" in pyproject
    assert "import-linter>=2.5" in pyproject
    assert "[tool.importlinter]" in pyproject
    assert 'type = "forbidden"' in pyproject
    assert "work_feed_mcp.integrations.upwork" in pyproject
    assert "work_feed_mcp.mcp_server" in pyproject
    assert "coverage:" in makefile
    assert "--cov-fail-under=80" in makefile
    assert "architecture:" in makefile
    assert "lint-imports" in makefile
    assert ".coverage coverage.xml htmlcov" in makefile
    assert "Run coverage gate" in workflow
    assert "make coverage" in workflow


def test_license_matches_project_metadata() -> None:
    license_text = read("LICENSE")
    pyproject = read("pyproject.toml")

    assert "MIT License" in license_text
    assert "work-feed-mcp maintainers" in license_text
    assert 'license = { text = "MIT" }' in pyproject


def test_contributing_and_security_keep_project_boundaries() -> None:
    contributing = read("CONTRIBUTING.md")
    security = read("SECURITY.md")
    combined = f"{contributing}\n{security}"

    for expected in [
        "make quality",
        "make architecture",
        "make coverage",
        "make smoke",
        "make e2e-smoke",
    ]:
        assert expected in contributing

    assert "import architecture contracts" in contributing
    assert "threshold starts conservatively at 80%" in contributing
    assert "Do not run live Upwork collection as part of normal verification" in contributing
    assert "GitHub private vulnerability reporting" in security
    assert "Collection diagnostics must stay redacted and secret-safe" in security

    boundary_phrases = [
        "backend ranking",
        "proposal/message generation",
        "auto-apply",
        "proxy",
        "cookie",
        "session",
        "access-control",
        "private GraphQL envelopes",
    ]
    lowered = combined.lower()
    for phrase in boundary_phrases:
        assert phrase.lower() in lowered


def test_github_templates_and_dependabot_are_present() -> None:
    for path in GITHUB_COMMUNITY_FILES:
        assert Path(path).exists(), path

    bug = read(".github/ISSUE_TEMPLATE/bug_report.md")
    feature = read(".github/ISSUE_TEMPLATE/feature_request.md")
    pr_template = read(".github/pull_request_template.md")
    dependabot = read(".github/dependabot.yml")

    assert "Do not include credentials, cookies, sessions" in bug
    assert "It does not add auto-apply, proposal/message generation" in feature
    assert "No auto-apply, proposal/message generation" in pr_template
    assert "package-ecosystem: github-actions" in dependabot
    assert "package-ecosystem: pip" in dependabot
    assert "interval: weekly" in dependabot


def test_changelog_and_release_docs_define_staged_release_path() -> None:
    changelog = read("CHANGELOG.md")
    releasing = read("docs/RELEASING.md")

    assert "## [Unreleased]" in changelog
    assert "## [0.1.0] - TBD" in changelog
    assert "First release checklist" in releasing
    assert "CHANGELOG.md" in releasing
    assert "GHCR is the primary package distribution surface" in releasing
    assert "PyPI publishing is deferred" in releasing
    assert "It does not publish to PyPI" in releasing
