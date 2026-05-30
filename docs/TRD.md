# Technical Requirements Document

## Status

This TRD describes current technical requirements and contracts for the
implemented system. It is intended for maintainers and coding agents working on
source changes.

## Technology Stack

- Language: Python >=3.11.
- Container runtime: Docker Compose.
- MCP server: `mcp` / FastMCP with Streamable HTTP in Docker.
- HTTP transport for live source collection: `curl-cffi`.
- Storage: SQLite.
- Package/dependency workflow: `uv`.
- Quality gates: ruff, mypy strict mode, import-linter, pytest, pytest-cov.

## Runtime Configuration

Runtime configuration is supplied through environment variables and persisted
collector config.

Docker/.env startup settings:

- `WORK_FEED_LIVE`
- `WORK_FEED_DB`
- `WORK_FEED_INTERVAL_SECONDS`
- `WORK_FEED_MAX_PAGES`
- `WORK_FEED_PAGE_SIZE`
- `WORK_FEED_QUERIES`
- `WORK_FEED_LOG_LEVEL`
- `WORK_FEED_MCP_HOST`
- `WORK_FEED_MCP_PORT`
- `WORK_FEED_MCP_PATH`
- `WORK_FEED_MCP_TRANSPORT`

Config precedence:

1. Worker startup seeds missing `collector_config` keys from Compose/.env.
2. Existing persisted keys survive restarts.
3. MCP `config_update` changes persisted keys through the command queue.
4. Live mode remains an environment/bootstrap setting.

## SQLite Requirements

### Schema Ownership

- The worker MUST initialize and maintain the runtime schema.
- MCP read paths MUST NOT create or migrate schema.
- MCP control paths MUST NOT create or migrate schema.
- Analytics CLI reads existing databases only.
- `scheduler-status` is a current diagnostic exception and may initialize schema.

### Required Tables

- `jobs`
- `job_skills`
- `collector_runs`
- `collector_run_results`
- `collector_config`
- `collector_commands`

### Schema Versioning

- Current `SCHEMA_VERSION` is `1`.
- Runtime must reject newer unsupported schemas.
- Any future schema change must include a migration/backward-compatibility
  decision before bumping schema version.

### Persistence Behavior

- Jobs are keyed by `job_id`.
- Ingestion inserts new jobs and skips existing jobs.
- Skills are stored in `job_skills` with `(job_id, skill)` as key.
- Run summaries are stored separately from jobs.
- Upstream private/raw payloads are not persisted.

## Collector Record Contract

The collector output contract is defined here so technical requirements and
data-contract guidance stay in one place.

Required public fields:

- `source`
- `id`
- `title`
- `description`
- `url`
- `skills`

Optional public fields:

- `posted_at`
- `job_type`
- `contractor_tier`
- `hourly_min`
- `hourly_max`
- `fixed_amount`
- `raw_id`

The domain validator MUST reject unsupported fields and known private/access
material field names such as cookie, session, token, proxy, and raw GraphQL
payload fields.

## Collection Requirements

- Fixture collection must work without live upstream access.
- Live collection requires explicit live mode.
- Live collection must classify blocked, rate-limited, temporary, and schema
  failures into useful collector errors.
- Diagnostics must redact credential-like values.
- Retry applies to temporary live collection failures, not arbitrary ingestion
  failures.
- A scheduled collection run may commit successful query results before a later
  query fails.

## MCP Tool Requirements

### Job Reads

- `jobs_recent(limit=20)`
- `jobs_search(title=None, skill=None, limit=20)`
- `jobs_get(job_id)`

Requirements:

- Enforce query limits through the service layer.
- Return JSON-safe dict payloads.
- Return `status: "empty"` for empty list results.
- Return `not_found` for missing single-job reads.
- Return `not_ready` when the worker-initialized database is unavailable or
  unsupported.

### Run and Status Reads

- `runs_recent(limit=5)`
- `collector_status()`

Requirements:

- Include recent runs and recent results.
- Include recent commands.
- Include effective config.
- Preserve redacted errors only.

### Control Tools

- `config_get()`
- `config_update(updates)`
- `collector_run_once()`
- `collector_pause()`
- `collector_resume()`
- `collector_command_status(command_id)`

Requirements:

- Control tools enqueue commands only.
- Control writes require an existing worker-initialized database.
- `config_update` accepts only:
  - `interval_seconds`
  - `queries`
  - `max_pages`
  - `page_size`
  - `paused`
- Commands have statuses:
  - `queued`
  - `running`
  - `applied`
  - `failed`

## CLI Requirements

The `work-feed` console script must provide:

- `collect`
- `ingest`
- `analytics`
- `collect-scheduled`
- `health`
- `scheduler-status`
- `worker`
- `mcp-server`
- `mcp-smoke`

CLI commands must return non-zero exit codes for invalid usage or runtime
failures. User-facing diagnostics must not leak credential material.

## Analytics Requirements

Analytics reads SQLite only. It must not perform live collection or infer missing
client fields from title or description text.

Current query groups:

- `summary`
- `skills`
- `jobs`
- `budgets`
- `clients`

Client dimensions absent from the current schema return unavailable
`unknown`/`null` buckets.

## Docker and Deployment Requirements

### Docker Compose

Compose must define:

- `work-feed-worker`
- `work-feed-mcp`
- `work-feed-data` shared volume

MCP port binding should remain local by default on the host.

### CI

CI must run fixture/local-contract checks and avoid live upstream collection.

CI must not deploy to private hosts or require private server secrets.

### Release

Release must:

- Trigger from version tags.
- Publish GHCR images.
- Create or update GitHub Release.
- Upload `release-manifest.json` and `checksums.txt`.
- Avoid live collection and private host deployment.

## Verification Requirements

Normal changes:

```bash
uv run --extra dev ruff format --check .
uv run --extra dev ruff check .
uv run --extra dev mypy src
uv run --extra dev lint-imports
uv run --extra dev pytest -q
```

Coverage-sensitive changes:

```bash
uv run --extra dev pytest --cov --cov-report=term-missing --cov-fail-under=80 -q
```

Fixture smoke:

```bash
uv run --extra dev work-feed collect --fixture tests/fixtures/visitor_job_search_response.json
```

Duplicate check:

```bash
npx jscpd --reporters ai --gitignore --min-lines 10 \
  --ignore "**/.venv/**,**/.mypy_cache/**,**/.pytest_cache/**,**/.ruff_cache/**,**/__pycache__/**,**/*.egg-info/**,**/uv.lock" .
```

Live evidence only with explicit opt-in:

```bash
WORK_FEED_LIVE=1 uv run --extra dev work-feed collect --live --query "python" --max-pages 1 --page-size 50
```

## Security Requirements

- Never commit secrets, cookies, sessions, tokens, private keys, proxy material,
  or runtime SQLite data.
- Do not document access-control bypasses or proxy acquisition.
- Redact collection diagnostics.
- Keep fixtures free of private upstream payloads unless explicitly sanitized
  and contract-appropriate.

## Known Technical Gaps

- No general schema migration framework beyond current v1 initialization and
  unsupported-newer-schema detection.
- No per-job observation history.
- No raw normalized payload archive.
- No query full-text index.
- Command claiming is designed around a single normal worker process.
