# ADR 0002: Worker-Owned SQLite Schema

## Status

Accepted

## Context

The worker, MCP server, analytics commands, and diagnostic commands all need
SQLite access. If every surface initialized or migrated schema on demand,
read-only agent paths could mutate runtime state and hide startup ordering
problems.

The readiness policy separates worker-owned initialization from MCP reads and
control writes.

## Decision

The worker owns SQLite schema initialization and runtime writes.

MCP read and control paths require an existing worker-initialized database. When
the database file is missing, required tables are absent, or the schema is newer
than this build supports, MCP tools return `not_ready` payloads instead of
creating schema.

`scheduler-status` is a current maintainer diagnostic exception and may
initialize schema.

## Consequences

Positive:

- Agent reads cannot silently create or migrate state.
- Startup ordering failures are visible through stable `not_ready` responses.
- Runtime authority is easier to reason about.

Tradeoffs:

- MCP server readiness depends on worker initialization.
- New schema changes need explicit migration planning.
- Diagnostic commands must be documented carefully when they have broader
  authority than MCP reads.

## Alternatives Considered

- Initialize schema from every surface: convenient, but mutates from read paths.
- Use a separate migration process: stronger long-term model, but not needed for
  the current v1 schema baseline.
- Store data outside SQLite: unnecessary for the current local data-engine
  scope.
