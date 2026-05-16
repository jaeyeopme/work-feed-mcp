# External LLM Guide: using the Upwork data engine

Use this guide when handing the repository to another LLM or coding agent. The goal is to keep the agent focused on the implemented Docker worker -> SQLite -> MCP flow, not on support automation, web backend work, or proposal generation.

## Copy-paste project brief

```text
You are helping with a Docker/MCP-first Upwork job discovery data engine.

Current structure:
- src/work_feed_mcp/services: collect, ingest, and analytics use cases.
- src/work_feed_mcp/repositories: SQLite query/persistence helpers.
- src/work_feed_mcp/db: SQLite schema/connection helpers.
- src/work_feed_mcp/domain: collector-record validation/domain types.
- src/work_feed_mcp/integrations/upwork: Upwork transport, credentials, GraphQL, normalization.
- src/work_feed_mcp/runtime: Docker worker runtime for recurring collection.
- src/work_feed_mcp/mcp_server: Streamable HTTP MCP server for agent usage.
- src/work_feed_mcp/cli: local/debug CLIs.
- tests: CLI/service tests and fixtures.

Product intent:
- Stable, deduplicated job storage for later external agent selection.
- Agents consume MCP tools for job lookup, status reads, and collector control.
- Not Upwork application automation.
- No auto-apply, proposal/message generation, backend ranking, or report delivery in the core data engine. Docker Compose is the primary runtime.

Hard boundaries:
- Keep Upwork collection dumb and secret-safe.
- Store only deduplicated jobs/job skills plus redacted scheduled-run summaries; do not store upstream GraphQL/private payloads, raw snapshots, or per-job observation logs.
- SQLite persistence belongs in ingestion/db/repository layers.
- Analytics reads SQLite only.
- Client analytics must not infer missing client fields from title/description. If client columns are absent, return unknown/null.
- Live collection requires explicit opt-in.

Use these docs as source of truth:
- README.md
- docs/LLM_CONTEXT.md
- docs/contracts/job-jsonl.md

Project-local Codex skill:
- skills/work-feed-jobs for read-only collected job lookup, filtering, and candidate summaries through MCP tools.
```

## What the current project can do

The project can run this local flow:

```text
Docker worker live collector input
  -> normalized job records/JSONL
  -> SQLite jobs/job_skills database
  -> basic JSON analytics queries
  -> MCP tools for agent usage
```

Primary Docker/MCP user flow:

```bash
cp .env.example .env
make up
make status
```

MCP endpoint for agents:

```text
http://127.0.0.1:8000/mcp
```

Core MCP tools:

```text
jobs_recent, jobs_search, jobs_get, runs_recent, collector_status,
config_get, config_update, collector_run_once, collector_pause,
collector_resume, collector_command_status
```

For Codex agents, prefer the bundled `skills/work-feed-jobs` skill for read-only job discovery prompts such as recent jobs, skill searches, collected job lookup, and candidate summaries.

Local/debug Python CLI commands still exist, but they are not the primary user onboarding path. Normal users should operate the Docker runtime through `make up`, `make status`, `make logs`, `make restart`, and `make down`.


## Verification commands

```bash
make quality
make smoke
make e2e-smoke
```

Duplicate check:

```bash
npx jscpd --reporters ai --gitignore --min-lines 10 \
  --ignore "**/.venv/**,**/.mypy_cache/**,**/.pytest_cache/**,**/.ruff_cache/**,**/__pycache__/**,**/*.egg-info/**,**/uv.lock,.omx/**" .
```

Live smoke is explicit opt-in only:

```bash
make live-smoke QUERY="python"
```

Default live smoke asks Upwork for 50 jobs in one visitor GraphQL page. Success means normalized output from this data engine, not scraper-owned SQLite rows or raw snapshots. Live evidence must be reported separately from local contract evidence. Do not add proxy acquisition, access-control bypass, or raw snapshot persistence guidance to this repo.

## Common wrong assumptions to correct

- “The project auto-applies to jobs.” Wrong. Auto-apply/message generation is out of scope.
- “The project ranks jobs in backend code.” Wrong. Ranking belongs in the consuming agent layer unless explicitly promoted later.
- “The project stores raw collection payloads or per-job observations.” Wrong. It stores unique jobs/skills plus redacted scheduled-run summaries only.
- “Analytics can infer client spend/country from text.” Wrong. Missing client fields become unknown/null.
- “Fixture tests prove live Upwork works.” Wrong. Fixture/local tests prove contracts only; live smoke is separate opt-in evidence.
- “New code should go under `packages/*`.” Wrong. New data-engine code should go under `src/work_feed_mcp`.

## Minimal context bundle to attach

1. `README.md`
2. `docs/LLM_CONTEXT.md`
3. `docs/EXTERNAL_LLM_GUIDE.md`
4. `docs/contracts/job-jsonl.md`
5. `docs/ORACLE_CLOUD_DEPLOY.md` for deployment workflow and server assumptions
6. `docs/RELEASING.md` for GitHub Release and GHCR package publishing behavior
7. `skills/work-feed-jobs/SKILL.md` for Codex job lookup behavior
8. Relevant source/tests under `src/work_feed_mcp` and `tests`.

Do not paste `.omx/logs`, `.omx/state`, or runtime traces unless the question is specifically about OMX execution.
