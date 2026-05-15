# LLM Context

## Project summary

This repository is a Docker/MCP-first local data engine for the Upwork job discovery pipeline. Agents are expected to use the MCP tools as the user-facing interface for collected job lookup, collector status, and safe collector control.

Primary app path:

```text
src/work_feed_mcp/services/            orchestration/use cases
src/work_feed_mcp/repositories/        SQLite query/persistence helpers
src/work_feed_mcp/db/                  SQLite schema/connection helpers
src/work_feed_mcp/domain/              domain validation/data types
src/work_feed_mcp/integrations/upwork/ Upwork transport + normalization
src/work_feed_mcp/runtime/             Docker worker runtime
src/work_feed_mcp/mcp_server/          agent-facing Streamable HTTP MCP server
src/work_feed_mcp/cli/                 local/debug CLI entrypoints
tests/                              CLI/service tests and fixtures
```

There is no longer a `packages/*` compatibility layer. New code should go under `src/work_feed_mcp`.

## Core flow

```text
Upwork visitor collection
  -> integrations/upwork.normalize
  -> services.scheduled_collection / services.ingestion
  -> SQLite `jobs` and `job_skills` tables
  -> services.analytics / repositories.analytics
  -> mcp_server tools for agent consumption
  -> optional local/debug CLI commands
```

Ingestion is deduplicating: existing `job_id` values are skipped and newly inserted jobs are returned as downstream selection candidates. Scheduled collection also stores operational summaries in `collector_runs` and `collector_run_results`; it does not store upstream raw payloads or per-job observation history.

## Boundaries

- Keep Upwork collection dumb and secret-safe.
- Do not store upstream GraphQL/private payloads, raw snapshots, or per-job observation logs. Scheduled run history is limited to redacted operational summaries.
- Do not run live Upwork collection unless the user explicitly opts in.
- Analytics reads SQLite only.
- Public runtime is Docker Compose + MCP first: a `work-feed-worker` container owns recurring collection and an `work-feed-mcp` container exposes agent-facing MCP tools over the shared SQLite DB.
- Ranking, reporting, notification, UI, REST-first API, internal LLM recommendation, proposal/message generation, and auto-apply are out of this repo's core data-engine scope.
- Recommendation/ranking belongs in the consuming agent layer unless explicitly promoted later.

## Verification

Use the root commands documented in `README.md` for local verification:

- `make quality`
- `make smoke`
- `make e2e-smoke`

Run live smoke only after explicit opt-in because it can contact Upwork.
