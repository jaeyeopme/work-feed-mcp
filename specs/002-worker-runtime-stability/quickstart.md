# Quickstart: Worker Runtime Stability

Use this after implementation to validate the feature.

## Narrow Tests

Run runtime and service tests first:

```bash
uv run --extra dev pytest -q tests/runtime tests/services tests/mcp_server tests/cli
```

Expected evidence:

- Scheduled worker failures do not terminate the worker loop.
- Manual `collector_run_once` failures mark the command failed.
- MCP tools return JSON-safe error payloads for not-ready, invalid request,
  storage, and internal failures, with `internal_error` exposing only
  `error_type` and a redacted short message.
- Scheduler/status read behavior does not initialize missing schema and returns
  parseable `not_ready` JSON with `reason`/`details` and exit code 2.

Run Docker/public contract tests:

```bash
uv run --extra dev pytest -q tests/docker
```

Expected evidence:

- README troubleshooting remains accurate.
- Docker/MCP public surface remains unchanged except for clarified stability
  behavior.

## Full Verification

Run repository gates:

```bash
uv run --extra dev ruff format --check .
uv run --extra dev ruff check .
uv run --extra dev mypy src
uv run --extra dev lint-imports
uv run --extra dev pytest -q
```

Optional coverage check:

```bash
uv run --extra dev pytest --cov --cov-report=term-missing --cov-fail-under=80 -q
```

## Manual Runtime Check

Start the Docker runtime:

```bash
cp .env.example .env
docker compose up -d --build
docker compose ps
```

Inspect status:

```bash
docker compose exec work-feed-worker work-feed scheduler-status --db /data/work-feed.sqlite
docker compose logs -f work-feed-worker
```

If upstream collection is blocked or unavailable, expected behavior is:

- the worker service remains running,
- run/status history records a failed run with redacted diagnostics,
- MCP control commands can still be queued and processed.

Live collection evidence is optional and must be reported separately:

```bash
WORK_FEED_LIVE=1 uv run --extra dev work-feed collect --live --query "python" --max-pages 1 --page-size 50
```

Do not use live upstream success or failure as a required normal verification
gate for this feature.
