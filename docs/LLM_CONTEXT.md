# LLM Context

## Project summary

This repository is a conventional Python/FastAPI backend organized around `src/upwork_app`.

Primary app path:

```text
src/upwork_app/main.py              FastAPI app
src/upwork_app/api/routes/          HTTP routes
src/upwork_app/schemas/             Pydantic API schemas
src/upwork_app/services/            orchestration/use cases
src/upwork_app/repositories/        SQLite query/persistence helpers
src/upwork_app/db/                  SQLite schema/connection helpers
src/upwork_app/domain/              domain validation/data types
src/upwork_app/integrations/upwork/ Upwork transport + normalization
src/upwork_app/cli/                 local CLI entrypoints
tests/                              API/service tests and fixtures
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
  -> CLI or FastAPI JSON response
```

Ingestion is deduplicating and jobs-only: existing `job_id` values are skipped, newly inserted jobs are returned as downstream selection candidates, and no run/observation/raw-record history is persisted.

## Boundaries

- Keep Upwork collection dumb and secret-safe.
- Do not store upstream GraphQL/private payloads, observation logs, or collection run history.
- Do not run live Upwork collection unless the user explicitly opts in.
- HTTP endpoints must use server-side DB settings and must not accept arbitrary caller-selected filesystem DB paths.
- Analytics reads SQLite only.
- Ranking, reporting, notification, UI, scheduler, and auto-apply are out of the MVP.

## Verification

Use the root commands documented in `README.md` for local verification:

- `make quality`
- `make smoke`
- `make e2e-smoke`

Run live smoke only after explicit opt-in because it can contact Upwork.
