from __future__ import annotations

from pathlib import Path

ROOT_OSS_FILES = [
    "LICENSE",
    "CONTRIBUTING.md",
    "CODE_OF_CONDUCT.md",
    "SECURITY.md",
    "CHANGELOG.md",
]

GITHUB_COMMUNITY_FILES = [
    ".github/ISSUE_TEMPLATE/bug_report.yml",
    ".github/ISSUE_TEMPLATE/feature_request.yml",
    ".github/ISSUE_TEMPLATE/config.yml",
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

    for expected in ["make quality", "make smoke", "make e2e-smoke"]:
        assert expected in contributing

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


def test_github_community_templates_and_dependabot_are_present() -> None:
    for path in GITHUB_COMMUNITY_FILES:
        assert Path(path).exists(), path

    bug = read(".github/ISSUE_TEMPLATE/bug_report.yml")
    feature = read(".github/ISSUE_TEMPLATE/feature_request.yml")
    pr_template = read(".github/pull_request_template.md")
    dependabot = read(".github/dependabot.yml")

    assert "Do not include credentials, cookies, sessions, proxy details" in bug
    assert "This does not add proposal/message generation or auto-apply behavior" in feature
    assert "No backend ranking or recommendation engine is added" in pr_template
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
