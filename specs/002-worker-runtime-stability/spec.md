# Feature Specification: Worker Runtime Stability

**Feature Branch**: `002-worker-runtime-stability`

**Created**: 2026-05-30

**Status**: Ready

**Input**: User description: "Stabilize the project before adding new source adapters such as Fiverr. Focus first on worker resilience, stable MCP error surfaces, and read-path ownership consistency."

## Clarifications

### Session 2026-05-30

- Q: Which scheduled-run failures should the worker swallow and continue after? → A: Expected operational collection failures only; this includes blocked, rate-limited, temporary/schema/network collector failures and run-history-recorded validation/ingestion failures, but not unexpected internal programming errors.
- Q: How should scheduler/status behave when the runtime database is not ready? → A: It should print a parseable `not_ready` JSON payload with more specific `reason`/`details` fields and exit with code 2.
- Q: How much detail should MCP internal error payloads expose? → A: They should include a stable `error_type` and a redacted short message, not full raw exception details.
- Q: How should the worker decide that a non-collector validation/ingestion failure is expected? → A: The decision is collection-service-boundary based: only failures raised by the scheduled collection service after that service has recorded a failed run/result are eligible to be swallowed by the worker; runtime loop, configuration, database connection, command-dispatch, or other programming errors outside that boundary must propagate.

## User Scenarios & Testing *(mandatory)*

### User Story 1 - Worker Survives Collection Failures (Priority: P1)

A local operator runs the Docker Compose runtime and upstream collection becomes blocked, rate limited, temporarily unavailable, or malformed. The worker records the failed run, keeps the runtime alive, and continues to process later commands and scheduled intervals.

**Why this priority**: A local Docker app is not operable if normal upstream failures terminate the long-running worker.

**Independent Test**: Simulate a scheduled collection failure and verify that the worker returns a successful runtime loop result, records the failure in run history, and remains able to process a subsequent command or iteration.

**Acceptance Scenarios**:

1. **Given** the worker is running an automatic scheduled collection, **When** collection fails with an upstream blocked error, **Then** the failed run is visible in status data and the worker continues running.
2. **Given** the worker has already recorded a failed scheduled run, **When** a pause/resume/config command is queued, **Then** the worker can still process the command.

---

### User Story 2 - Manual Collection Commands Fail Safely (Priority: P2)

An MCP client queues `collector_run_once` and collection fails. The command reaches a terminal `failed` state with redacted error information, while the worker remains alive for future commands.

**Why this priority**: Manual control commands are agent-facing and must be auditable without turning expected upstream failures into process failures.

**Independent Test**: Queue a manual run command with a collector that fails and verify that command status becomes `failed`, redacted error text contains no credential-like values, and the worker can process a later command.

**Acceptance Scenarios**:

1. **Given** a queued `collector_run_once` command, **When** collection fails, **Then** the command status is `failed` and includes a redacted error type/message.
2. **Given** a failed `collector_run_once` command, **When** another command is queued afterward, **Then** that later command can still be processed normally.
3. **Given** the worker is paused and a `collector_run_once` command is queued, **When** that manual collection fails, **Then** the command reaches `failed` and the paused scheduled state does not turn into an automatic run.

---

### User Story 3 - MCP Tools Return JSON-Safe Operational Errors (Priority: P2)

An MCP client calls read or control tools while storage is locked, unavailable, or otherwise fails unexpectedly. The tool returns a stable JSON-safe error payload instead of surfacing an unstructured protocol exception.

**Why this priority**: Agent-facing tools need predictable JSON responses for operational failures so users can troubleshoot without parsing transport-level exceptions.

**Independent Test**: Force a storage error through an MCP tool helper and verify the result is a JSON-safe `ok: false` payload with a bounded error category and redacted message.

**Acceptance Scenarios**:

1. **Given** an MCP read tool encounters a SQLite/storage failure, **When** the tool is called, **Then** it returns `ok: false` with a stable storage error category.
2. **Given** an MCP tool encounters an unexpected exception, **When** the tool is called, **Then** it returns `ok: false` with a stable internal error category, a stable `error_type`, a redacted short message, and no raw exception details or secret-like diagnostic material.

---

### User Story 4 - Read Paths Do Not Mutate Runtime State (Priority: P3)

A local operator runs status/read commands against a missing or uninitialized database. Read paths report not-ready or unavailable status without creating or migrating schema.

**Why this priority**: The architecture states that the worker owns SQLite schema initialization and read paths should not mutate runtime state.

**Independent Test**: Run scheduler/status read behavior against a missing or schema-less database and verify that it does not create the runtime schema.

**Acceptance Scenarios**:

1. **Given** no database exists, **When** a status read is requested, **Then** the response prints parseable `not_ready` JSON with specific `reason`/`details`, exits with code 2, and does not create a database.
2. **Given** an empty database file exists without the runtime schema, **When** a status read is requested, **Then** the response prints parseable `not_ready` JSON with specific `reason`/`details`, exits with code 2, and does not initialize tables.

### Edge Cases

- A scheduled collection fails after one query succeeded and a later query failed.
- A manual run command fails while the worker is currently paused.
- A collection failure message contains credential-like values such as tokens, cookies, sessions, proxy URLs, or authorization headers.
- A storage error occurs while reading command status or recent jobs.
- A database exists with an unsupported future schema version.
- The worker receives a stop signal while sleeping or polling commands.
- The MCP server starts before the worker initializes SQLite.
- An unexpected internal programming error occurs outside the expected collection failure path.

## Requirements *(mandatory)*

### Functional Requirements

- **FR-001**: The worker MUST continue running after expected operational collection failures during scheduled automatic runs, including blocked, rate-limited, temporary/schema/network collector failures and validation/ingestion failures that the scheduled collection service has already recorded as failed run history.
- **FR-002**: The worker MUST record failed scheduled automatic runs in run/status history with failure type and redacted diagnostic text.
- **FR-003**: The worker MUST preserve completed query results when a later query fails during the same run.
- **FR-004**: A failed scheduled automatic run MUST NOT prevent later queued commands from being processed.
- **FR-005**: A failed manual `collector_run_once` command MUST reach a terminal `failed` command state, including when the worker is currently paused.
- **FR-006**: Manual command failures MUST include redacted error details and MUST NOT expose credential-like or raw upstream material.
- **FR-007**: MCP read and control tools MUST return JSON-safe `ok: false` payloads for not-ready, invalid request, storage, and unexpected internal errors.
- **FR-008**: MCP error payloads MUST use stable error categories that are suitable for agent troubleshooting.
- **FR-009**: MCP error payloads MUST redact credential-like values from all diagnostic messages.
- **FR-010**: Read/status paths MUST NOT initialize or migrate SQLite runtime schema unless explicitly documented as a worker-owned write path.
- **FR-011**: The project MUST preserve the worker-owned schema/write/recurrence and MCP read/enqueue-only control architecture.
- **FR-012**: Live upstream collection evidence remains explicit opt-in and is not required for normal verification.
- **FR-013**: The worker MUST NOT silently swallow unexpected internal programming errors that occur outside the expected operational collection failure path.
- **FR-014**: Scheduler/status read commands MUST output parseable `not_ready` JSON with specific `reason` and `details` fields and exit with code 2 when the runtime database is missing, schema-less, or unsupported.
- **FR-015**: MCP `internal_error` payloads MUST include a stable `error_type` and redacted short message but MUST NOT include full raw exception details.

### Key Entities *(include if feature involves data)*

- **Collector Run**: A recorded automatic or manual collection attempt with status, trigger, totals, failure type, and redacted diagnostic details.
- **Collector Command**: A queued MCP control command with queued/running/applied/failed state and optional redacted failure details.
- **MCP Error Payload**: A JSON-safe operational response containing `ok: false`, a stable error category, optional `error_type`, and bounded redacted diagnostic fields.
- **Runtime Database Readiness**: The state of the SQLite file and schema as seen by read/control paths.
- **Affected Layers**: `runtime`, `services`, `repositories`, `mcp_server`, `cli`, `db`.
- **Data Contracts**: `collector_runs`, `collector_run_results`, `collector_commands`, MCP tool payloads, scheduler/status CLI output, README troubleshooting text.

## Success Criteria *(mandatory)*

### Measurable Outcomes

- **SC-001**: In simulated scheduled upstream failure tests, the worker completes its loop without process failure and records a failed run.
- **SC-002**: In simulated manual run failure tests, the command reaches `failed` and a later command can still be processed.
- **SC-003**: MCP tool tests prove storage and unexpected errors return JSON-safe payloads rather than unhandled exceptions.
- **SC-004**: Read/status tests prove missing or schema-less databases are not mutated by read paths.
- **SC-005**: Redaction tests prove credential-like values and raw exception details are absent from run history, command failures, and MCP error payloads.
- **SC-006**: Scheduler/status tests prove not-ready cases return parseable JSON with specific `reason`/`details` fields and exit code 2.
- **SC-007**: Relevant fixture/local verification commands pass: targeted pytest suites, formatting/lint/type/import checks, coverage, fixture smoke, and e2e smoke using direct `uv`/CLI commands.

## Assumptions

- The current worker-owned SQLite schema model remains the architecture.
- Expected upstream failures include blocked, rate-limited, temporary, schema, and network failure classes already represented by collector errors.
- Fixture/local tests are sufficient for normal verification; live collection remains a separate opt-in activity.
- Network/proxy policy is not changed by this feature except that any diagnostics must remain redacted.
- Adding new source adapters such as Fiverr is out of scope until the runtime stability behavior is settled.
