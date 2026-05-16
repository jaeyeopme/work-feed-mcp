#!/usr/bin/env bash
set -euo pipefail

: "${EVENT_NAME:?missing EVENT_NAME}"
: "${GITHUB_REF_VALUE:?missing GITHUB_REF_VALUE}"

output_result() {
  local value="$1"
  if [[ -n "${GITHUB_OUTPUT:-}" ]]; then
    echo "deploy_relevant=${value}" >> "$GITHUB_OUTPUT"
  fi
  echo "deploy_relevant=${value}"
}

matches_deploy_path() {
  case "$1" in
    src/*|pyproject.toml|uv.lock|Dockerfile|compose.yaml|.github/workflows/*|scripts/deploy/*)
      return 0
      ;;
    *)
      return 1
      ;;
  esac
}

if [[ "$EVENT_NAME" == "pull_request" ]]; then
  echo "pull_request never deploys"
  output_result false
  exit 0
fi

if [[ "$EVENT_NAME" == "workflow_dispatch" ]]; then
  if [[ "$GITHUB_REF_VALUE" != "refs/heads/main" ]]; then
    echo "workflow_dispatch deploys are main-only; got ${GITHUB_REF_VALUE}" >&2
    exit 1
  fi
  output_result true
  exit 0
fi

if [[ "$GITHUB_REF_VALUE" != "refs/heads/main" ]]; then
  echo "non-main push never deploys: ${GITHUB_REF_VALUE}"
  output_result false
  exit 0
fi

: "${GITHUB_SHA:?missing GITHUB_SHA for push deploy decision}"
before="${GITHUB_EVENT_BEFORE:-}"

if [[ -z "$before" || "$before" =~ ^0+$ ]]; then
  changed="$(git ls-tree -r --name-only HEAD)"
elif git cat-file -e "$before^{commit}" 2>/dev/null; then
  changed="$(git diff --name-only "$before" "$GITHUB_SHA")"
else
  echo "before commit ${before} is unavailable; checking the target tree"
  changed="$(git ls-tree -r --name-only HEAD)"
fi

for path in $changed; do
  if matches_deploy_path "$path"; then
    output_result true
    exit 0
  fi
done

output_result false
