#!/usr/bin/env bash
set -Eeuo pipefail

require_env() {
  local name="$1"
  if [[ -z "${!name:-}" ]]; then
    echo "missing required environment variable: ${name}" >&2
    exit 1
  fi
}

require_env ORACLE_DEPLOY_PATH
require_env DEPLOY_SHA
require_env PREVIOUS_SHA

cd "$ORACLE_DEPLOY_PATH"

git cat-file -e "${DEPLOY_SHA}^{commit}"
git cat-file -e "${PREVIOUS_SHA}^{commit}"

current_sha="$(git rev-parse HEAD)"
if [[ "$current_sha" != "$DEPLOY_SHA" ]]; then
  echo "deploy checkout mismatch: expected ${DEPLOY_SHA}, got ${current_sha}" >&2
  exit 1
fi

rollback_armed=false
rollback() {
  local status=$?
  trap - ERR
  if [[ "$rollback_armed" != "true" ]]; then
    exit "$status"
  fi

  echo "deploy failed for ${DEPLOY_SHA}; attempting rollback to ${PREVIOUS_SHA}" >&2
  set +e
  git reset --hard "$PREVIOUS_SHA"
  local reset_status=$?
  docker compose up -d --build --remove-orphans
  local compose_status=$?
  docker compose ps
  local ps_status=$?
  set -e

  if [[ "$reset_status" -eq 0 && "$compose_status" -eq 0 && "$ps_status" -eq 0 ]]; then
    echo "rollback to ${PREVIOUS_SHA} completed" >&2
  else
    echo "rollback to ${PREVIOUS_SHA} failed: reset=${reset_status} compose=${compose_status} ps=${ps_status}" >&2
  fi
  exit "$status"
}
trap rollback ERR
rollback_armed=true

docker compose config >/tmp/work-feed-compose-config.yaml
docker compose up -d --build --remove-orphans
docker compose ps
docker compose exec -T work-feed-worker work-feed health --role worker --db /data/work-feed.sqlite
docker compose exec -T work-feed-mcp sh -c 'work-feed health --role mcp --db /data/work-feed.sqlite --http-url "http://127.0.0.1:${WORK_FEED_MCP_PORT:-8000}${WORK_FEED_MCP_PATH:-/mcp}"'
docker compose exec -T work-feed-mcp sh -c 'work-feed mcp-smoke --url "http://127.0.0.1:${WORK_FEED_MCP_PORT:-8000}${WORK_FEED_MCP_PATH:-/mcp}"'
docker compose exec -T work-feed-worker work-feed scheduler-status --db /data/work-feed.sqlite

rollback_armed=false
echo "deploy ${DEPLOY_SHA} completed successfully"
