# LLM Context

## Project summary

This repository is a CLI-first local data engine for the Upwork job discovery pipeline. OpenClaw or another agent layer is expected to act as the user interface/orchestrator.

Primary app path:

```text
src/upwork_app/services/            orchestration/use cases
src/upwork_app/repositories/        SQLite query/persistence helpers
src/upwork_app/db/                  SQLite schema/connection helpers
src/upwork_app/domain/              domain validation/data types
src/upwork_app/integrations/upwork/ Upwork transport + normalization
src/upwork_app/cli/                 local CLI entrypoints
tests/                              CLI/service tests and fixtures
scripts/                            local operational helpers
```

There is no longer a `packages/*` compatibility layer. New code should go under `src/upwork_app`.

## Core flow

```text
Upwork fixture/live response
  -> integrations/upwork.normalize
  -> normalized job JSONL
  -> services.ingestion / repositories.ingestion / db.schema
  -> SQLite `jobs` and `job_skills` tables
  -> services.analytics / repositories.analytics
  -> CLI JSON output for OpenClaw/agent consumption
  -> optional one-shot scheduled collection CLI invoked by OS scheduler
```

Ingestion is deduplicating: existing `job_id` values are skipped and newly inserted jobs are returned as downstream selection candidates. Scheduled collection also stores operational summaries in `collector_runs` and `collector_run_results`; it does not store upstream raw payloads or per-job observation history.

## Boundaries

- Keep Upwork collection dumb and secret-safe.
- Do not store upstream GraphQL/private payloads, raw snapshots, or per-job observation logs. Scheduled run history is limited to redacted operational summaries.
- Do not run live Upwork collection unless the user explicitly opts in.
- Analytics reads SQLite only.
- Public runtime is Docker Compose + MCP first: a `collector-worker` container owns recurring collection and an `upwork-collector-mcp` container exposes agent-facing MCP tools over the shared SQLite DB. Native/legacy scheduler execution remains outside the app core; OS schedulers may call one-shot CLI commands such as `collect-scheduled`.
- Ranking, reporting, notification, UI, REST-first API, internal LLM recommendation, proposal/message generation, and auto-apply are out of this repo's core data-engine scope.
- Recommendation/ranking belongs in OpenClaw skills unless explicitly promoted later.

## Verification

Use the root commands documented in `README.md` for local verification:

- `make quality`
- `make smoke`
- `make e2e-smoke`

Run live smoke only after explicit opt-in because it can contact Upwork.
