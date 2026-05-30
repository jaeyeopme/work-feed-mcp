from __future__ import annotations

from pathlib import Path


def _workflow() -> str:
    return Path(".github/workflows/release.yml").read_text()


def test_release_workflow_publishes_github_release_and_ghcr_image() -> None:
    workflow = _workflow()

    assert "name: release" in workflow
    assert "tags:" in workflow
    assert '"v*.*.*"' in workflow
    assert "workflow_dispatch:" in workflow
    assert "contents: write" in workflow
    assert "packages: write" in workflow
    assert "actions/checkout@v6" in workflow
    assert "docker login ghcr.io" in workflow
    assert "docker build" in workflow
    assert "docker push" in workflow
    assert "gh release create" in workflow
    assert "release-manifest.json" in workflow
    assert "checksums.txt" in workflow
    assert "gh release upload" in workflow
    assert "preserving release notes" in workflow


def test_release_workflow_uses_versioned_ghcr_tags_and_metadata() -> None:
    workflow = _workflow()

    assert "ghcr.io/${REPOSITORY,,}" in workflow
    assert '"${IMAGE}:${TAG}"' in workflow
    assert '"${IMAGE}:${VERSION}"' in workflow
    assert '"${IMAGE}:latest"' in workflow
    assert "org.opencontainers.image.source" in workflow
    assert "org.opencontainers.image.description" in workflow
    assert "org.opencontainers.image.licenses=MIT" in workflow
    assert "org.opencontainers.image.revision" in workflow
    assert "docker buildx imagetools inspect" in workflow
    assert "default_mcp_endpoint" in workflow


def test_release_workflow_validates_tags_and_avoids_live_or_deploy_side_effects() -> None:
    workflow = _workflow()

    assert "release tags must look like vMAJOR.MINOR.PATCH" in workflow
    assert "^v[0-9]+\\.[0-9]+\\.[0-9]+" in workflow
    assert "make live-smoke" not in workflow
    assert "WORK_FEED_LIVE=1" not in workflow
    assert "ssh oracle-work-feed" not in workflow
    assert "ssh " not in workflow
    assert "docker compose up" not in workflow
    assert "ORACLE_SSH" not in workflow
    assert "ORACLE_DEPLOY_PATH" not in workflow
    assert 'gh release edit "$TAG" --title "$TAG" --notes' not in workflow


def test_changelog_keeps_release_notes_surface() -> None:
    docs = Path("CHANGELOG.md").read_text()

    assert "## [Unreleased]" in docs
    assert "## [0.1.0] - TBD" in docs
    assert "GHCR" in docs
