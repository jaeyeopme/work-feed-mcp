# Product Requirements Document

## Status

This PRD describes the current implemented product surface of `work-feed-mcp`.
It is derived from `README.md`, `docs/TRD.md`, `CONTRIBUTING.md`,
`SECURITY.md`, tests, and the current source layout.

## Product Summary

`work-feed-mcp` is a Docker/MCP-first local data engine for collecting
authorized public job-listing records, storing normalized records in SQLite, and
exposing scoped MCP tools for agent consumption.

The product separates source collection, durable local storage, and agent-facing
access. It is not a hosted SaaS app, browser automation product, proposal
generator, recommendation backend, or auto-apply system.

## Users

Primary users:

- A local operator who runs the Docker Compose runtime.
- An agent or MCP client that reads already-collected jobs and collector status.
- A maintainer who debugs collection, ingestion, schema, and release flows.

Secondary users:

- A maintainer publishing public release artifacts.

## Goals

- Run a local Docker Compose runtime with a worker and MCP server.
- Collect authorized public job-listing records in a secret-safe way.
- Normalize source responses into a stable JSONL-compatible job contract.
- Deduplicate persisted jobs by `job_id`.
- Store normalized jobs, skills, run summaries, config, and queued commands in
  SQLite.
- Expose MCP tools for job lookup, run/status reads, and safe queued collector
  control.
- Keep fixture/local verification separate from live upstream evidence.

## Non-Goals

The product does not provide:

- REST-first API.
- UI or notification delivery.
- Backend recommendation/ranking engine.
- Proposal, message, or cover-letter generation.
- Auto-apply or application automation.
- Cookie/session/proxy acquisition guidance.
- Access-control bypass playbooks.
- Raw upstream private GraphQL payload persistence.
- Per-job observation history.

## Current User Journeys

### UJ-001: Start the Runtime

As a local operator, I can copy `.env.example`, start Docker Compose with
`docker compose up -d --build`, and inspect runtime status with
`docker compose ps`.

Acceptance:

- Docker Compose starts `work-feed-worker`.
- Docker Compose starts `work-feed-mcp`.
- Both services share the same SQLite volume.
- MCP is bound to a local host port.

### UJ-002: Connect an MCP Client

As an agent operator, I can connect an MCP client to
`http://127.0.0.1:8000/mcp` and call job/status tools.

Acceptance:

- The endpoint is Streamable HTTP MCP, not REST.
- `jobs_recent(limit=5)` returns a JSON-safe response.
- An empty initialized database returns an empty success payload, not an error.
- A missing or uninitialized database returns a `not_ready` payload.

### UJ-003: Query Collected Jobs

As an agent, I can list recent jobs, search jobs by title or exact normalized
skill, and fetch one job by `job_id`.

Acceptance:

- `jobs_recent` returns newest jobs by first-seen time.
- `jobs_search` supports title substring and exact normalized skill filters.
- `jobs_get` returns one job or a `not_found` error.
- Responses include job fields and normalized skills.

### UJ-004: Inspect Collector Status

As an agent or operator, I can inspect the latest run, recent runs, recent
results, recent commands, and effective config.

Acceptance:

- `collector_status` returns status, recent run data, commands, and config.
- `runs_recent` returns run history.
- Run errors are redacted.

### UJ-005: Queue Safe Collector Control

As an agent, I can enqueue pause/resume/run-once/config-update commands without
directly mutating the worker's current run.

Acceptance:

- Control tools return immediately with `command_id` and `queued` status.
- Worker applies commands between collection runs.
- `collector_command_status` reports queued, running, applied, or failed.
- `config_update` accepts only mutable runtime config keys.
- Live/non-live mode cannot be switched by MCP control tools.

### UJ-006: Maintain and Release

As a maintainer, I can run fixture/local gates, release GHCR images from tags,
and keep normal CI limited to verification.

Acceptance:

- Normal verification includes quality, coverage, fixture smoke, and e2e smoke checks.
- Live collection evidence is explicit opt-in only.
- Release publishes GitHub Release and GHCR image tags.
- Normal CI does not deploy to a private host or require private server secrets.

## Functional Requirements

- PRD-FR-001: The system MUST expose Docker Compose services for worker and MCP
  server runtime.
- PRD-FR-002: The worker MUST own recurring collection and SQLite writes.
- PRD-FR-003: The MCP server MUST read and control the shared SQLite runtime
  through scoped tools.
- PRD-FR-004: The collector MUST normalize source responses into the documented
  job JSONL contract.
- PRD-FR-005: Ingestion MUST deduplicate by `job_id`.
- PRD-FR-006: The system MUST store run summaries separately from job records.
- PRD-FR-007: The system MUST redact credential-like values in persisted
  diagnostics.
- PRD-FR-008: MCP read/control paths MUST return stable `not_ready` payloads
  when the worker has not initialized the database.
- PRD-FR-009: MCP control paths MUST enqueue commands instead of applying worker
  state directly.
- PRD-FR-010: Agent-facing job lookup MUST operate on already-collected data.
- PRD-FR-011: Live collection evidence MUST be reported separately from
  fixture/local contract evidence.

## Product Boundaries

The project intentionally keeps recommendations and job-fit ranking outside the
core data engine. Consuming agents may rank or summarize retrieved rows, but the
backend does not persist scores or own proposal/application workflows.

The project also intentionally avoids raw upstream payload archives. If future
features need richer data, they must first update the normalized collector
contract, schema, and safety rules.

## Success Criteria

- A fresh Docker runtime can be started with `docker compose up -d --build` and
  inspected with `docker compose ps`.
- An MCP client can connect to the documented endpoint and call `jobs_recent`.
- Fixture collection produces valid JSONL.
- Fixture JSONL can be ingested into SQLite.
- Analytics commands can summarize the fixture-ingested database.
- Architecture contracts remain valid through import-linter.
- Unit and integration tests pass in normal verification.

## Open Questions

- Should future schema versions add proper migrations, or keep schema v1 until a
  concrete data-contract change exists?
- Should query performance be upgraded with SQLite FTS or batched skill loading
  when local datasets grow?
- Should spec-kit baseline specs mirror every current subsystem, or only future
  behavior-changing work?
