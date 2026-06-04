# ADR 0003: MCP Control Tools Enqueue Commands

## Status

Accepted

## Context

Agents need limited control over the collector runtime: pause, resume, run once,
and update mutable schedule/query configuration. Direct mutation from MCP tools
would couple agent calls to worker internals and could interrupt active
collection runs.

## Decision

MCP control tools enqueue commands in SQLite. The worker polls the command queue
and applies commands between collection runs.

Control tools return immediately with a `command_id` and `queued` status.
Callers use `collector_command_status` to observe queued, running, applied, or
failed states.

## Consequences

Positive:

- Agent control is auditable.
- Worker remains the authority for runtime state changes.
- Control calls are fast and JSON-safe.
- Commands can preserve failure details with redacted errors.

Tradeoffs:

- Control is asynchronous.
- Callers must poll for terminal status.
- The current command queue assumes one normal worker process.

## Alternatives Considered

- Apply commands directly from MCP: simpler, but crosses runtime authority
  boundaries.
- Add a separate control service: more moving parts than current scope requires.
- Use filesystem signals or process signals: less auditable than persisted
  command rows.
