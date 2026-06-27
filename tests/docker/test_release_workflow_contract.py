from __future__ import annotations

from pathlib import Path


def _workflow() -> str:
    return Path(".github/workflows/release.yml").read_text()


def test_release_workflow_has_safe_publish_contract() -> None:
    workflow = _workflow()

    for expected in [
        "name: release",
        "tags:",
        '"v*.*.*"',
        "workflow_dispatch:",
        "contents: write",
        "packages: write",
        "docker login ghcr.io",
        "docker push",
        "gh release create",
        "gh release upload",
        "release-manifest.json",
        "checksums.txt",
    ]:
        assert expected in workflow


def test_release_workflow_validates_tags_and_avoids_live_or_deploy_side_effects() -> None:
    workflow = _workflow()

    for expected in [
        "release tags must look like vMAJOR.MINOR.PATCH",
        "^v[0-9]+\\.[0-9]+\\.[0-9]+",
    ]:
        assert expected in workflow

    for forbidden in [
        "make live-smoke",
        "WORK_FEED_LIVE=1",
        "ssh ",
        "docker compose up",
        "ORACLE_SSH",
        "ORACLE_DEPLOY_PATH",
    ]:
        assert forbidden not in workflow
