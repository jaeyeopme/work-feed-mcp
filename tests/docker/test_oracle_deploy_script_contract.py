from __future__ import annotations

from pathlib import Path


def _script() -> str:
    return Path("scripts/deploy/oracle-compose-deploy.sh").read_text()


def test_oracle_deploy_script_exists_and_is_shell_hardened() -> None:
    script_path = Path("scripts/deploy/oracle-compose-deploy.sh")
    script = _script()

    assert script_path.exists()
    assert script_path.stat().st_mode & 0o111
    assert script.startswith("#!/usr/bin/env bash")
    assert "set -Eeuo pipefail" in script


def test_oracle_deploy_script_requires_and_validates_deploy_state() -> None:
    script = _script()

    for variable in ["ORACLE_DEPLOY_PATH", "DEPLOY_SHA", "PREVIOUS_SHA"]:
        assert f"require_env {variable}" in script
    assert 'git cat-file -e "${DEPLOY_SHA}^{commit}"' in script
    assert 'git cat-file -e "${PREVIOUS_SHA}^{commit}"' in script
    assert "git rev-parse HEAD" in script
    assert '"$current_sha" != "$DEPLOY_SHA"' in script


def test_oracle_deploy_script_rolls_back_with_previous_sha() -> None:
    script = _script()

    assert "rollback_armed=false" in script
    assert "trap rollback ERR" in script
    assert "rollback_armed=true" in script
    assert 'git reset --hard "$PREVIOUS_SHA"' in script
    assert "deploy failed for ${DEPLOY_SHA}; attempting rollback to ${PREVIOUS_SHA}" in script
    assert "rollback to ${PREVIOUS_SHA} completed" in script


def test_oracle_deploy_script_runs_compose_health_and_mcp_smoke() -> None:
    script = _script()

    assert "docker compose config >/tmp/work-feed-compose-config.yaml" in script
    assert "docker compose up -d --build --remove-orphans" in script
    assert "docker compose ps" in script
    assert "work-feed health --role worker" in script
    assert "work-feed health --role mcp" in script
    assert "work-feed mcp-smoke" in script
    assert "work-feed scheduler-status" in script


def test_oracle_deploy_script_preserves_runtime_boundaries() -> None:
    script = _script().lower()

    assert "git clean" not in script
    assert "live-smoke" not in script
    assert "work_feed_live=1" not in script
    assert "rm .env" not in script
    assert "compose.override.yaml" not in script
