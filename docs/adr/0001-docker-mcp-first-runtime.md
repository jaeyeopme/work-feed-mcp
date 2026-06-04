# ADR 0001: Docker/MCP-First Runtime

## Status

Accepted

## Context

The project needs a local runtime that collects job records, persists them, and
exposes them to coding agents. Direct CLI commands, a REST API, or an
application-native scheduler would all work technically, but the product is a
local data engine consumed through MCP.

The implemented runtime uses Docker Compose with two services:

- `work-feed-worker`
- `work-feed-mcp`

Both services share a SQLite Docker volume.

## Decision

The primary runtime is Docker Compose plus MCP:

```text
work-feed-worker -> SQLite volume -> work-feed-mcp -> MCP client
```

Direct Python CLI commands remain available for local debugging, smoke checks,
and maintainer operations. They are not the normal user interface.

## Consequences

Positive:

- Agent clients get a stable MCP endpoint.
- Collection and agent reads run as separate processes.
- SQLite state is durable through a Docker volume.
- Normal operation is simpler than coordinating ad hoc CLI commands.

Tradeoffs:

- Users need Docker Compose for the normal path.
- Health checks and MCP protocol smoke are separate concepts.
- Local CLI commands must stay aligned with Docker behavior without becoming the
  product's primary interface.

## Alternatives Considered

- CLI-first workflow: simpler to implement, but worse for long-running agent
  consumption.
- REST API: familiar, but the product is agent/MCP-facing and not a REST app.
- Systemd scheduler: useful for one deployment shape, but less portable than
  Docker Compose for the current scope.
