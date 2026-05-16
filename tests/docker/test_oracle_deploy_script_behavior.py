from __future__ import annotations

import os
import subprocess
from pathlib import Path

from tests.docker.deploy_contract_helpers import commit_file, init_git_repo, run_git

SCRIPT = Path("scripts/deploy/oracle-compose-deploy.sh").resolve()


def _init_deploy_repo(tmp_path: Path) -> tuple[Path, str, str, Path]:
    repo = init_git_repo(tmp_path)
    previous = commit_file(repo, "app.txt", "previous\n")
    deploy = commit_file(repo, "app.txt", "deploy\n")
    fake_bin = tmp_path / "bin"
    fake_bin.mkdir()
    (fake_bin / "docker").write_text(
        "#!/usr/bin/env bash\n"
        'echo "$*" >> "$DOCKER_LOG"\n'
        'if [[ "${FAIL_MCP_SMOKE:-0}" == "1" && "$*" == *"work-feed mcp-smoke"* ]]; then\n'
        "  exit 42\n"
        "fi\n"
    )
    (fake_bin / "docker").chmod(0o755)
    return repo, previous, deploy, fake_bin


def _run_script(
    repo: Path, previous: str, deploy: str, fake_bin: Path, *, fail_mcp_smoke: bool = False
) -> subprocess.CompletedProcess[str]:
    env = os.environ | {
        "ORACLE_DEPLOY_PATH": str(repo),
        "PREVIOUS_SHA": previous,
        "DEPLOY_SHA": deploy,
        "DOCKER_LOG": str(fake_bin.parent / "docker.log"),
        "FAIL_MCP_SMOKE": "1" if fail_mcp_smoke else "0",
        "PATH": f"{fake_bin}:{os.environ['PATH']}",
    }
    return subprocess.run(
        ["bash", str(SCRIPT)], cwd=repo, env=env, text=True, capture_output=True, check=False
    )


def test_oracle_deploy_script_runs_health_checks_without_rollback(tmp_path: Path) -> None:
    repo, previous, deploy, fake_bin = _init_deploy_repo(tmp_path)

    result = _run_script(repo, previous, deploy, fake_bin)

    assert result.returncode == 0, result.stderr
    docker_log = (tmp_path / "docker.log").read_text()
    assert "compose config" in docker_log
    assert "compose up -d --build --remove-orphans" in docker_log
    assert "work-feed health --role worker" in docker_log
    assert "work-feed health --role mcp" in docker_log
    assert "work-feed mcp-smoke" in docker_log
    assert "work-feed scheduler-status" in docker_log
    assert run_git(repo, "rev-parse", "HEAD") == deploy


def test_oracle_deploy_script_rolls_back_to_previous_sha_on_post_deploy_failure(
    tmp_path: Path,
) -> None:
    repo, previous, deploy, fake_bin = _init_deploy_repo(tmp_path)

    result = _run_script(repo, previous, deploy, fake_bin, fail_mcp_smoke=True)

    assert result.returncode == 42
    assert f"attempting rollback to {previous}" in result.stderr
    assert run_git(repo, "rev-parse", "HEAD") == previous
    docker_log = (tmp_path / "docker.log").read_text()
    assert docker_log.count("compose up -d --build --remove-orphans") == 2
    assert "compose ps" in docker_log


def test_oracle_deploy_script_does_not_arm_rollback_for_invalid_target_checkout(
    tmp_path: Path,
) -> None:
    repo, previous, deploy, fake_bin = _init_deploy_repo(tmp_path)
    subprocess.run(["git", "reset", "--hard", previous], cwd=repo, check=True)

    result = _run_script(repo, previous, deploy, fake_bin)

    assert result.returncode != 0
    assert "deploy checkout mismatch" in result.stderr
    assert "attempting rollback" not in result.stderr
    assert not (tmp_path / "docker.log").exists()
    assert run_git(repo, "rev-parse", "HEAD") == previous
