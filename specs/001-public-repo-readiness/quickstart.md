# Quickstart: Public Repository Readiness

Use this to validate the feature after implementation.

## Public User Flow

From a fresh checkout, README should guide a user through this shape:

```bash
git clone <repository-url>
cd work-feed-mcp
cp .env.example .env
docker compose up -d --build
docker compose ps
```

The README should then show common operation commands:

```bash
docker compose logs -f
docker compose restart
docker compose down
docker compose exec work-feed-worker work-feed scheduler-status --db /data/work-feed.sqlite
```

## Contract Checks

Search active public surfaces for private deployment traces:

```bash
rg -n "Oracle|ORACLE_|oracle|/home/ubuntu|deploy-oracle|oracle-work-feed|ORACLE_SSH|ORACLE_DEPLOY_PATH|rollback" README.md .github scripts docs
```

Expected result:

- No active public workflow or script performs private Oracle/server deployment.
- No test requires Oracle/private deploy scripts, workflows, or docs to exist.
- Any remaining non-private use of words such as `rollback` must not describe a maintainer server runbook.

Check README counter coverage:

```bash
rg -n "seen|inserted|skipped|job_id|dedupe|deduplicat" README.md
```

Expected result:

- README defines `seen`, `inserted`, `skipped`, and `job_id` deduplication.

## Verification

Run narrow public-surface tests first:

```bash
uv run --extra dev pytest -q tests/docker
```

Then run repository gates when implementation is complete:

```bash
uv run --extra dev ruff format --check .
uv run --extra dev ruff check .
uv run --extra dev mypy src
uv run --extra dev lint-imports
uv run --extra dev pytest -q
```

Live collection evidence is out of scope for this feature and must not be used as normal verification.
