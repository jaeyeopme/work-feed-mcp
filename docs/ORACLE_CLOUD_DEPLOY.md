# Oracle Cloud deployment

This repository currently has CI in `.github/workflows/quality.yml` and CD in `.github/workflows/deploy-oracle.yml`.

## What deploy-oracle does

On pushes to `main`, and on manual `workflow_dispatch`, the workflow:

1. Runs `make quality`, `make smoke`, and `make e2e-smoke`.
2. SSHes into the Oracle Cloud instance.
3. Fetches `origin/main` in the existing deploy checkout.
4. Resets the checkout to the GitHub commit SHA.
5. Runs `docker compose up -d --build --remove-orphans`.
6. Verifies worker health, MCP health, and scheduler status.

The deploy command intentionally does **not** run `git clean`, so server-local files such as `compose.override.yaml` and `.env` remain intact.

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
- The deploy path is already a clone of this repository.
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
docker compose exec -T work-feed-worker work-feed scheduler-status --db /data/work-feed.sqlite
```
