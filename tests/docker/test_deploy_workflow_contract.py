from __future__ import annotations

from pathlib import Path


def test_oracle_deploy_workflow_runs_verify_then_ssh_deploy() -> None:
    workflow = Path(".github/workflows/deploy-oracle.yml").read_text()

    assert "name: deploy-oracle" in workflow
    assert "branches: [main]" in workflow
    assert "workflow_dispatch:" in workflow
    assert "needs: verify" in workflow
    assert "environment: oracle-cloud" in workflow
    assert "ORACLE_SSH_HOST" in workflow
    assert "ORACLE_SSH_USER" in workflow
    assert "ORACLE_SSH_KEY" in workflow
    assert "ORACLE_DEPLOY_PATH" in workflow
    assert "make quality" in workflow
    assert "make smoke" in workflow
    assert "make e2e-smoke" in workflow
    assert "git fetch --prune origin main" in workflow
    assert 'git reset --hard "$DEPLOY_SHA"' in workflow
    assert "docker compose up -d --build --remove-orphans" in workflow
    assert "work-feed health --role worker" in workflow
    assert "work-feed health --role mcp" in workflow
    assert "work-feed mcp-smoke" in workflow
    assert "work-feed scheduler-status" in workflow
    assert "git clean" not in workflow


def test_oracle_deploy_docs_describe_required_secrets() -> None:
    docs = Path("docs/ORACLE_CLOUD_DEPLOY.md").read_text()

    for secret in [
        "ORACLE_SSH_HOST",
        "ORACLE_SSH_USER",
        "ORACLE_SSH_KEY",
        "ORACLE_SSH_PORT",
        "ORACLE_DEPLOY_PATH",
    ]:
        assert secret in docs
    assert "compose.override.yaml" in docs
    assert "docker compose up -d --build --remove-orphans" in docs
