# Oracle Cloud deployment

This repository uses a single GitHub Actions workflow for CI/CD:

- `.github/workflows/ci-cd.yml`

The workflow keeps verification and deployment in one pipeline, but deployment is a separate job that runs only after the `quality` job succeeds.

## What ci-cd does

For every push and pull request, the workflow runs fixture/local-contract verification:

1. `make quality`
2. `make smoke`
3. `make e2e-smoke`

For Oracle Cloud deployment, the workflow then runs `deploy-oracle` only when one of these conditions is true:

- `workflow_dispatch` is started from `main`; or
- a push to `main` changes runtime/deploy-infrastructure files such as `src/**`, `pyproject.toml`, `uv.lock`, `Dockerfile`, `compose.yaml`, `.github/workflows/**`, or `scripts/deploy/**`.

Docs-only, tests-only, skills-only, and `.omx`-only changes still run CI, but they do **not** auto-deploy to Oracle Cloud. Use manual dispatch from `main` if an operator intentionally wants to redeploy without a runtime file change. Manual dispatch from non-`main` refs fails clearly instead of silently skipping deployment.

## Deploy flow

The deploy job:

1. Validates required GitHub environment secrets.
2. Configures SSH for the Oracle instance.
3. SSHes into the existing server checkout.
4. Captures `PREVIOUS_SHA` before changing the checkout.
5. Fetches `origin/main`, checks out `main`, and resets to the GitHub commit SHA.
6. Runs `scripts/deploy/oracle-compose-deploy.sh` from the target checkout.
7. The script validates `DEPLOY_SHA` and `PREVIOUS_SHA`, runs Docker Compose config/build/up, then verifies worker health, MCP health, MCP protocol smoke, and scheduler status.

The deploy path intentionally does **not** run `git clean`, so server-local files such as `compose.override.yaml` and `.env` remain intact.

## Automatic rollback

`oracle-compose-deploy.sh` uses `PREVIOUS_SHA` as a best-effort rollback anchor. If a post-deploy Compose, health, MCP smoke, or scheduler-status step fails after the target checkout is validated, the script attempts to:

1. reset the checkout back to `PREVIOUS_SHA`;
2. run `docker compose up -d --build --remove-orphans`;
3. print `docker compose ps` diagnostics.

Rollback is best-effort. Host-level failures such as Docker daemon failure, disk exhaustion, or broken server Git auth can still require manual operator recovery.

## Required GitHub environment and secrets

Create a GitHub Environment named `oracle-cloud` and add these secrets:

| Secret | Example | Notes |
| --- | --- | --- |
| `ORACLE_SSH_HOST` | `168.107.37.234` | Oracle instance public IP or DNS name. |
| `ORACLE_SSH_USER` | `ubuntu` | SSH user on the Oracle instance. |
| `ORACLE_SSH_KEY` | private key text | Private key with access to the instance. |
| `ORACLE_SSH_PORT` | `22` | Optional; defaults to `22`. |
| `ORACLE_DEPLOY_PATH` | `/home/ubuntu/work-feed-mcp` | Existing checkout path on the instance. |

For the current Oracle instance, the deploy path observed during local verification was `/home/ubuntu/work-feed-mcp`.

## Server assumptions

- Docker and Docker Compose are installed on the Oracle instance.
- The deploy path is already a clone of this private repository.
- The server checkout can fetch `origin/main`.
- Runtime-only files are managed on the server, not in git.
- The Docker volume `work-feed-data` stores the SQLite database and is preserved across deploys.

## Manual rollback

From the Oracle instance:

```bash
cd /home/ubuntu/work-feed-mcp
git fetch origin
git reset --hard <known-good-sha>
docker compose up -d --build --remove-orphans
docker compose ps
```

## Post-deploy checks

```bash
docker compose exec -T work-feed-worker work-feed health --role worker --db /data/work-feed.sqlite
docker compose exec -T work-feed-mcp work-feed health --role mcp --db /data/work-feed.sqlite --http-url http://127.0.0.1:8000/mcp
docker compose exec -T work-feed-mcp work-feed mcp-smoke --url http://127.0.0.1:8000/mcp
docker compose exec -T work-feed-worker work-feed scheduler-status --db /data/work-feed.sqlite
```

CI/CD verification never runs `make live-smoke` or live Upwork collection. It checks local fixture contracts and the already-running Docker/MCP service health only.
