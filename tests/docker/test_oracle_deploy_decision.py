from __future__ import annotations

import os
import subprocess
from pathlib import Path

from tests.docker.deploy_contract_helpers import commit_file, init_git_repo, run_git

SCRIPT = Path("scripts/deploy/should-deploy-oracle.sh").resolve()


def _run_decision(
    repo: Path, *, event: str, ref: str, before: str = ""
) -> subprocess.CompletedProcess[str]:
    sha = run_git(repo, "rev-parse", "HEAD")
    env = os.environ | {
        "EVENT_NAME": event,
        "GITHUB_REF_VALUE": ref,
        "GITHUB_EVENT_BEFORE": before,
        "GITHUB_SHA": sha,
    }
    return subprocess.run(
        ["bash", str(SCRIPT)], cwd=repo, env=env, text=True, capture_output=True, check=False
    )


def test_pull_request_never_deploys_even_for_runtime_change(tmp_path: Path) -> None:
    repo = init_git_repo(tmp_path)
    before = run_git(repo, "rev-parse", "HEAD")
    commit_file(repo, "src/work_feed_mcp/example.py", "print('runtime')\n")

    result = _run_decision(repo, event="pull_request", ref="refs/pull/1/merge", before=before)

    assert result.returncode == 0
    assert "deploy_relevant=false" in result.stdout


def test_main_push_runtime_change_deploys(tmp_path: Path) -> None:
    repo = init_git_repo(tmp_path)
    before = run_git(repo, "rev-parse", "HEAD")
    commit_file(repo, "src/work_feed_mcp/example.py", "print('runtime')\n")

    result = _run_decision(repo, event="push", ref="refs/heads/main", before=before)

    assert result.returncode == 0
    assert "deploy_relevant=true" in result.stdout


def test_main_push_docs_only_change_does_not_deploy(tmp_path: Path) -> None:
    repo = init_git_repo(tmp_path)
    before = run_git(repo, "rev-parse", "HEAD")
    commit_file(repo, "docs/ORACLE_CLOUD_DEPLOY.md", "docs only\n")

    result = _run_decision(repo, event="push", ref="refs/heads/main", before=before)

    assert result.returncode == 0
    assert "deploy_relevant=false" in result.stdout


def test_all_zero_first_push_checks_tree_for_runtime_files(tmp_path: Path) -> None:
    repo = init_git_repo(tmp_path)
    commit_file(repo, "compose.yaml", "services: {}\n")

    result = _run_decision(repo, event="push", ref="refs/heads/main", before="0" * 40)

    assert result.returncode == 0
    assert "deploy_relevant=true" in result.stdout


def test_workflow_dispatch_is_main_only(tmp_path: Path) -> None:
    repo = init_git_repo(tmp_path)

    main = _run_decision(repo, event="workflow_dispatch", ref="refs/heads/main")
    branch = _run_decision(repo, event="workflow_dispatch", ref="refs/heads/feature")

    assert main.returncode == 0
    assert "deploy_relevant=true" in main.stdout
    assert branch.returncode != 0
    assert "main-only" in branch.stderr
