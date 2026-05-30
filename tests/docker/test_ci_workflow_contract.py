from __future__ import annotations

from pathlib import Path


def _workflow() -> str:
    return Path(".github/workflows/ci-cd.yml").read_text()


def test_ci_workflow_is_verification_only() -> None:
    workflow = _workflow()

    assert Path(".github/workflows/ci-cd.yml").exists()
    assert not Path(".github/workflows/quality.yml").exists()
    assert not Path(".github/workflows/deploy-oracle.yml").exists()
    assert "name: ci" in workflow
    assert "pull_request:" in workflow
    assert "push:" in workflow
    assert "workflow_dispatch:" in workflow
    assert "permissions:" in workflow
    assert "contents: read" in workflow
    assert "defaults:" in workflow
    assert "shell: bash" in workflow
    assert "timeout-minutes:" in workflow

    assert "quality:" in workflow
    assert "make quality" in workflow
    assert "make coverage" in workflow
    assert "make smoke" in workflow
    assert "make e2e-smoke" in workflow

    assert "changes:" not in workflow
    assert "deploy_relevant" not in workflow
    assert "deploy-oracle:" not in workflow
    assert "scripts/deploy/" not in workflow
    assert "ssh " not in workflow
    assert "known_hosts" not in workflow
    assert "ORACLE_" not in workflow
    assert "environment:" not in workflow
    assert "docker compose up" not in workflow
    assert "make live-smoke" not in workflow
