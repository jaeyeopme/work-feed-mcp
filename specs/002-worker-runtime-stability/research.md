# Research: Worker Runtime Stability

## Decision: Expected operational collection failures are recorded and swallowed by the worker loop

**Rationale**: Upstream blocked, rate-limited, temporary, schema, and network
failures are normal operational states for a live collector. Validation and
ingestion failures that `collect_scheduled` can record in run history are also
operational collection failures from the worker's perspective. The long-running
worker should use that persisted evidence and continue rather than exiting the
Docker process. Unexpected internal programming errors outside that expected
collection path should still surface instead of being silently swallowed.

**Alternatives considered**:

- Let Docker restart the worker after each failure: rejected because repeated
  restart loops hide command processing behavior and obscure status.
- Force `collect_scheduled` never to raise: rejected because CLI one-shot commands
  still need meaningful exit codes and tests already rely on fail-fast service
  behavior.
- Catch every exception in the worker loop: rejected because it can hide coding
  defects and corrupted runtime assumptions.

## Decision: Manual `collector_run_once` failures remain command failures

**Rationale**: A manual run is an explicit queued command. If its collection
fails, the command should reach `failed` so MCP clients can poll and understand
the result. The existing `_apply_command` command failure path already models
this shape and should be preserved.

**Alternatives considered**:

- Mark failed manual collection commands as applied with a failed run result:
  rejected because it hides command-level failure.
- Retry manual commands forever: rejected because command queue progress would
  be blocked by upstream state.

## Decision: MCP tools return bounded JSON-safe operational errors

**Rationale**: Agent-facing tools should return structured payloads for expected
runtime states. Existing behavior already handles `not_ready` and invalid
request errors; extending that pattern to storage and internal failures keeps
MCP clients from receiving unstructured protocol exceptions for local operational
problems.

**Alternatives considered**:

- Let all unexpected exceptions propagate through MCP: rejected because agents
  lose stable troubleshooting fields and redaction guarantees.
- Convert every error to the same category: rejected because users need to
  distinguish invalid input, runtime not ready, storage failure, and internal
  failure.

MCP internal errors should include a stable `error_type` plus a redacted short
message. Full raw exception details should not be returned through MCP payloads.

## Decision: Scheduler/status read paths must not initialize schema

**Rationale**: The architecture says worker owns schema initialization and MCP
read/control paths use an existing worker-initialized database. The CLI status
command should match that mental model instead of creating tables as a side
effect of a read. When the runtime database is not ready, it should print
parseable `not_ready` JSON with specific `reason` and `details` fields and exit
with code 2.

**Alternatives considered**:

- Keep scheduler/status as a special write-capable debug command: rejected
  because README presents it as an operational read command.
- Remove scheduler/status CLI: rejected because README and operators use it for
  local inspection.

## Decision: No schema migration for this feature

**Rationale**: Existing `collector_runs`, `collector_run_results`, and
`collector_commands` tables already carry status, error type, and redacted error
fields. Stability can be implemented as behavior and error-surface changes.

**Alternatives considered**:

- Add a dedicated worker health table: rejected as unnecessary until there is a
  user-visible need beyond current run/status and command history.

## Decision: No live upstream evidence in normal verification

**Rationale**: The feature can be tested with simulated collector failures,
SQLite readiness states, and MCP helper tests. Live upstream behavior is
unstable and requires explicit opt-in.

**Alternatives considered**:

- Require live smoke for stability completion: rejected because public CI and
  normal local validation must remain deterministic.
