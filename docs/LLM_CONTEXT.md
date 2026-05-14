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

Ingestion is deduplicating and jobs-only: existing `job_id` values are skipped, newly inserted jobs are returned as downstream selection candidates, and no run/observation/raw-record history is persisted.

## Boundaries

- Keep Upwork collection dumb and secret-safe.
- Do not store upstream GraphQL/private payloads, observation logs, or collection run history.
- Do not run live Upwork collection unless the user explicitly opts in.
- Analytics reads SQLite only.
- Scheduler/background execution is outside the app core; OS scheduler should call one-shot CLI commands such as `collect-scheduled`. The repo may provide CLI contracts/templates for OS scheduler setup, but not an app-native daemon.
- Ranking, reporting, notification, UI, app-native scheduler daemon, proposal/message generation, and auto-apply are out of this repo's core data-engine scope.
- Recommendation/ranking belongs in OpenClaw skills unless explicitly promoted later.

## Verification

Use the root commands documented in `README.md` for local verification:

- `make quality`
- `make smoke`
- `make e2e-smoke`

Run live smoke only after explicit opt-in because it can contact Upwork.
