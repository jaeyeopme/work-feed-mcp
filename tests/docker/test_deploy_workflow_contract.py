from __future__ import annotations

from pathlib import Path


def _workflow() -> str:
    return Path(".github/workflows/ci-cd.yml").read_text()


def _decision_script() -> str:
    return Path("scripts/deploy/should-deploy-oracle.sh").read_text()


def test_ci_cd_workflow_replaces_split_ci_and_deploy_workflows() -> None:
    workflow = _workflow()

    assert Path(".github/workflows/ci-cd.yml").exists()
    assert not Path(".github/workflows/quality.yml").exists()
    assert not Path(".github/workflows/deploy-oracle.yml").exists()
    assert "name: ci-cd" in workflow
    assert "pull_request:" in workflow
    assert "push:" in workflow
    assert "workflow_dispatch:" in workflow
    assert "permissions:" in workflow
    assert "contents: read" in workflow
    assert "defaults:" in workflow
    assert "shell: bash" in workflow
    assert "timeout-minutes:" in workflow


def test_quality_job_is_the_single_verification_gate() -> None:
    workflow = _workflow()

    assert "quality:" in workflow
    assert "make quality" in workflow
    assert "make smoke" in workflow
    assert "make e2e-smoke" in workflow
    assert "deploy-oracle:" in workflow
    assert "needs: [quality, changes]" in workflow
    assert "verify:" not in workflow


def test_deploy_job_is_main_or_manual_and_job_gated() -> None:
    workflow = _workflow()

    assert "changes:" in workflow
    assert "deploy_relevant" in workflow
    assert "if: needs.changes.outputs.deploy_relevant == 'true'" in workflow
    decision_script = _decision_script()
    assert "GITHUB_REF_VALUE" in workflow
    assert "refs/heads/main" in decision_script
    assert "workflow_dispatch deploys are main-only" in decision_script
    assert "pull_request never deploys" in decision_script
    assert "on:\n  push:\n  pull_request:" in workflow
    assert "paths:" not in workflow


def test_deploy_path_gating_excludes_docs_tests_and_skills_only_changes() -> None:
    workflow = _workflow()
    decision_script = _decision_script()

    for deploy_path in [
        "src/*",
        "pyproject.toml",
        "uv.lock",
        "Dockerfile",
        "compose.yaml",
        ".github/workflows/*",
        "scripts/deploy/*",
    ]:
        assert deploy_path in decision_script

    assert "docs/*" not in decision_script
    assert "tests/*" not in decision_script
    assert "skills/*" not in decision_script
    assert "run: scripts/deploy/should-deploy-oracle.sh" in workflow
    assert "github.event.before" in workflow
    assert "github.sha" in workflow


def test_oracle_deploy_keeps_secret_environment_and_minimal_bootstrap() -> None:
    workflow = _workflow()

    assert "environment: oracle-cloud" in workflow
    for secret in [
        "ORACLE_SSH_HOST",
        "ORACLE_SSH_USER",
        "ORACLE_SSH_KEY",
        "ORACLE_SSH_PORT",
        "ORACLE_DEPLOY_PATH",
    ]:
        assert secret in workflow
    assert 'PREVIOUS_SHA="$(git rev-parse HEAD)"' in workflow
    assert "git fetch --prune origin main" in workflow
    assert 'git reset --hard "$DEPLOY_SHA"' in workflow
    assert "bash scripts/deploy/oracle-compose-deploy.sh" in workflow
    assert "docker compose up -d --build --remove-orphans" not in workflow
    assert "work-feed mcp-smoke" not in workflow
    assert "git clean" not in workflow
    assert "make live-smoke" not in workflow
