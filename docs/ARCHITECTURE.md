# Architecture

## Status

This document describes the implemented architecture. Use it when changing
runtime boundaries, data flow, persistence, MCP tools, or release behavior.

It is derived from the public docs, source layout, tests, and release workflow.

## System Overview

`work-feed-mcp` runs as two Docker Compose services backed by one SQLite
database in a shared Docker volume:

```text
External source
  -> work-feed-worker
  -> SQLite Docker volume
  -> work-feed-mcp
  -> Agent / MCP client
```

The worker owns collection, ingestion, schema initialization, and recurring
runtime behavior. The MCP server exposes Streamable HTTP MCP tools. Those tools
read the same SQLite database and enqueue control commands for the worker to
apply later.

## Runtime Components

### work-feed-worker

Responsibilities:

- Load runtime settings from environment.
- Initialize the SQLite schema.
- Seed persisted runtime config defaults.
- Run recurring scheduled collection.
- Poll and apply queued collector commands.
- Persist jobs, skills, run summaries, and command results.

Entry points:

- Docker command: `work-feed worker`
- Source: `src/work_feed_mcp/runtime/worker.py`

### work-feed-mcp

Responsibilities:

- Start a FastMCP server.
- Expose Streamable HTTP MCP at the configured path.
- Provide job lookup tools, status tools, config tools, and enqueue-only control
  tools.
- Return stable JSON-safe errors for not-ready or invalid requests.

Entry points:

- Docker command: `work-feed mcp-server`
- Source: `src/work_feed_mcp/mcp_server/server.py`

### SQLite Database

Responsibilities:

- Store normalized jobs and skills.
- Store collector run summaries and per-query run results.
- Store collector config and queued commands.

The database is shared storage, not shared authority. Each surface gets only the
access it needs:

| Surface | Authority | Schema initialization |
| --- | --- | --- |
| Worker | Read/write runtime owner | Yes |
| MCP read | Read-only existing DB | No |
| MCP control | Existing DB command writes | No |
| Analytics CLI | Read-only diagnostics | No |
| Scheduler status CLI | Maintainer diagnostics | Yes, current exception |

## Internal Layers

```text
src/work_feed_mcp/
├── integrations/upwork/
├── domain/
├── db/
├── repositories/
├── services/
├── runtime/
├── mcp_server/
└── cli/
```

### integrations/upwork

Owns source-specific behavior:

- GraphQL request shape.
- Visitor-mode transport.
- Credential references and redaction.
- Upwork response normalization into JSONL-safe job models.

It does not own SQLite persistence, MCP behavior, runtime scheduling, or agent
selection logic.

### domain

Owns canonical collector record validation:

- Required and optional public fields.
- Field normalization.
- Secret/private-field rejection.
- Content hash generation.

It remains independent from infrastructure layers.

### db

Owns SQLite schema and connection policy:

- Schema version.
- Table and index declarations.
- Worker/read/control connection helpers.
- Readiness helper for required tables.

### repositories

Owns SQLite persistence and query helpers:

- Insert jobs and skills.
- Query recent/search/get jobs.
- Store run history.
- Store config and commands.
- Run analytics aggregations.

Repositories do not import services, runtime, MCP, CLI, or source integration
code.

### services

Owns application use cases:

- Collection orchestration.
- JSONL ingestion.
- Scheduled collection.
- MCP-safe job queries.
- Collector control readiness and command enqueueing.
- Run/status reads.
- Analytics service.
- Retry policy.

Services are below interface adapters and must not depend on CLI or MCP modules.

### runtime

Owns the long-running worker process:

- Signal handling.
- Loop/sleep behavior.
- Command polling.
- Command application.
- Collection execution using persisted config.

### mcp_server

Owns MCP adapter registration and thin tool wrappers:

- FastMCP server creation.
- MCP tool registration.
- JSON-safe wrapper around service calls.

Business logic belongs in services, not in the adapter.

### cli

Owns local/debug entrypoints:

- `collect`
- `ingest`
- `analytics`
- `collect-scheduled`
- `health`
- `scheduler-status`
- `worker`
- `mcp-server`
- `mcp-smoke`

CLI commands are useful for local maintenance but are not the normal user
interface. Normal operation is Docker/MCP-first.

## Data Flow

### Scheduled Collection

```text
Worker loop
  -> effective config
  -> services.scheduled_collection.collect_scheduled
  -> services.collector.collect_jobs
  -> integrations.upwork.collect_live or fixture loader
  -> integrations.upwork.normalize_response
  -> domain.validate_payload
  -> repositories.ingestion.insert_job_if_new
  -> repositories.run_history
```

Completed per-query results are committed as the run progresses. If a later
query fails, the worker records that failure but does not roll back earlier
successful query results from the same run.

### MCP Job Reads

```text
MCP tool
  -> mcp_server.tools
  -> services.job_queries
  -> services.collector_control.ensure_ready_read
  -> repositories.jobs
  -> SQLite read-only connection
```

The read path does not initialize the schema. Missing or incompatible databases
return `not_ready`.

### MCP Control

```text
MCP control tool
  -> mcp_server.tools
  -> services.collector_control
  -> ensure_ready_control
  -> repositories.collector_control.enqueue_command
  -> SQLite collector_commands
  -> worker polls and applies command
```

Control tools enqueue commands only. The worker applies commands between
collection runs and records terminal command status.

## Runtime and Release Architecture

Normal local runtime:

```text
docker compose up -d --build
```

Services:

- `work-feed-worker`
- `work-feed-mcp`
- `work-feed-data` Docker volume

Public release path:

- GitHub Actions validates quality through CI.
- Version tags may publish GHCR images and GitHub Release artifacts.
- Release publishing does not start or mutate a private runtime.

## Architecture Constraints

- Source collection stays dumb and secret-safe.
- Raw upstream private payloads are not persisted.
- MCP is not REST.
- MCP read/control paths do not initialize schema.
- Agent-facing control is queued and auditable.
- Ranking and proposal generation stay outside the core data engine.
- Live collection is not part of normal verification.

## Known Hotspots

- `services/scheduled_collection.py` currently concentrates orchestration,
  retry, transaction, run-history, and error-recording policy.
- Schema migration is minimal because current schema version is still v1.
- Job search is simple SQLite filtering and may need batching/FTS when data
  volume grows.
- Command queue assumes one worker process in normal Compose runtime.
