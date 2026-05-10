# LLM Context

## Project summary

This repository is now organized as a conventional Python/FastAPI backend around `src/upwork_app`.

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
```

Legacy package path remains mostly as compatibility shims for historical imports/tests:

```text
packages/collector   legacy collector compatibility package
packages/ingest      legacy ingest compatibility package
packages/analytics   legacy analytics compatibility package
packages/ranker      future placeholder
packages/report      future placeholder
```

## Core flow

```text
Upwork fixture/live response
  -> integrations/upwork.normalize
  -> normalized job JSONL
  -> services.ingestion / db.schema
  -> SQLite tables
  -> services.analytics / repositories.analytics
  -> CLI or FastAPI JSON response
```

## Boundaries

- Keep Upwork collection dumb and secret-safe.
- Do not store upstream GraphQL/private payloads in raw records.
- Do not run live Upwork collection unless the user explicitly opts in.
- Analytics reads SQLite only.
- Ranking, reporting, notification, UI, scheduler, and auto-apply are out of the MVP.

## Verification

Prefer root app checks for new work:

```bash
make app-quality
make app-smoke
make e2e-smoke
```

Run full compatibility checks before claiming broad completion:

```bash
make quality
make smoke
```
