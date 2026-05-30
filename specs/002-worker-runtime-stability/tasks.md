# Tasks: Worker Runtime Stability

**Input**: Design documents from `specs/002-worker-runtime-stability/`

**Prerequisites**: `plan.md`, `spec.md`, `research.md`, `data-model.md`, `contracts/runtime-stability.md`, `quickstart.md`

**Tests**: Included because this feature changes runtime behavior, MCP/CLI public contracts, and failure handling. Live upstream tests remain explicit opt-in and are out of scope for normal verification.

**Organization**: Tasks are grouped by user story to enable independent implementation and testing.

## Format: `[ID] [P?] [Story] Description`

- **[P]**: Can run in parallel because it touches different files or only reads files
- **[Story]**: User story label, present only in user story phases
- Every task names the exact repository path(s) it touches or verifies

## Phase 1: Setup (Shared Inventory)

**Purpose**: Establish current runtime failure and readiness behavior before edits.

- [X] T001 [P] Run baseline targeted tests for `tests/runtime/test_worker.py`, `tests/mcp_server/test_tools.py`, `tests/mcp_server/test_not_ready.py`, `tests/services/test_scheduler_status.py`, and `tests/cli/test_scheduler_status_cli.py`
- [X] T002 [P] Inspect current failure/readiness paths in `src/work_feed_mcp/runtime/worker.py`, `src/work_feed_mcp/mcp_server/tools.py`, `src/work_feed_mcp/services/scheduler_status.py`, `src/work_feed_mcp/services/collector_control.py`, and `src/work_feed_mcp/db/connection.py`

---

## Phase 2: Foundational (Shared Readiness Payload)

**Purpose**: Add shared not-ready detail support that later MCP and CLI stories can reuse.

**Critical**: Complete before User Story 3 and User Story 4 because both depend on stable not-ready payload details.

- [X] T003 [P] Add not-ready `details` assertions in `tests/mcp_server/test_not_ready.py` for `db_missing`, `schema_missing`, and `unsupported_schema`
- [X] T004 Update `NotReadyError` and `not_ready_payload` in `src/work_feed_mcp/services/collector_control.py` to include specific safe `details` text
- [X] T005 Run `uv run --extra dev pytest -q tests/mcp_server/test_not_ready.py`

**Checkpoint**: Shared readiness payloads include `reason`, `details`, and `next_action` without mutating read paths.

---

## Phase 3: User Story 1 - Worker Survives Collection Failures (Priority: P1) MVP

**Goal**: Scheduled automatic collection failures that are expected operational collection failures are recorded and do not terminate the worker loop.

**Independent Test**: Simulate scheduled collection failures in `WorkerRuntime` and verify failed run evidence remains available while later commands or iterations can still run.

### Tests for User Story 1

- [X] T006 [US1] Add runtime tests in `tests/runtime/test_worker.py` proving scheduled expected operational collection failures are swallowed, failed run history remains queryable, a later queued command can still be processed, and stop requests while sleeping or polling still exit cleanly
- [X] T007 [US1] Add runtime test in `tests/runtime/test_worker.py` proving unexpected internal programming errors outside the expected collection failure path are not silently swallowed
- [X] T008 [P] [US1] Review and extend existing partial-failure assertions in `tests/services/test_scheduled_collection.py` to cover validation/ingestion failures recorded by `src/work_feed_mcp/services/scheduled_collection.py` before being exposed to the worker predicate

### Implementation for User Story 1

- [X] T009 [US1] Add an expected operational collection failure predicate across `src/work_feed_mcp/runtime/worker.py` and `src/work_feed_mcp/services/scheduled_collection.py` that covers collector failures and validation/ingestion failures only after scheduled collection has recorded failed run history
- [X] T010 [US1] Update scheduled automatic collection handling in `src/work_feed_mcp/runtime/worker.py` to redact and continue after expected operational failures while preserving stop, command polling, and `max_iterations` behavior and still propagating runtime/config/database programming errors outside the collection-service boundary
- [X] T011 [US1] Update troubleshooting text in `README.md` so upstream blocked/unavailable states say the worker remains running and records failed run history
- [X] T012 [US1] Run `uv run --extra dev pytest -q tests/runtime/test_worker.py tests/services/test_scheduled_collection.py`

**Checkpoint**: User Story 1 is independently complete when scheduled operational failures no longer terminate the worker and the README no longer describes this as a future follow-up.

---

## Phase 4: User Story 2 - Manual Collection Commands Fail Safely (Priority: P2)

**Goal**: `collector_run_once` failures transition the command to `failed` with redacted diagnostics and do not stop the worker from processing later commands.

**Independent Test**: Queue a manual run command that fails, poll command status, and verify a later command can still transition normally.

### Tests for User Story 2

- [X] T013 [US2] Add runtime tests in `tests/runtime/test_worker.py` proving failed `collector_run_once` commands reach `failed`, include redacted diagnostics, allow a later command to be processed, and fail safely when the worker is paused
- [X] T014 [P] [US2] Add repository command-status assertions in `tests/repositories/test_collector_control.py` for failed command `error_type` and `redacted_error` payload shape

### Implementation for User Story 2

- [X] T015 [US2] Update command failure handling in `src/work_feed_mcp/runtime/worker.py` to preserve redacted failure details, continue processing later commands, and keep paused scheduled collection behavior unchanged after a failed `run_once`
- [X] T016 [US2] Verify `collector_control.mark_failed` and `command_status` in `src/work_feed_mcp/repositories/collector_control.py` return JSON-safe failed command details without leaking raw values
- [X] T017 [US2] Run `uv run --extra dev pytest -q tests/runtime/test_worker.py tests/repositories/test_collector_control.py`

**Checkpoint**: User Story 2 is independently complete when manual run failures are terminal command failures, not worker failures.

---

## Phase 5: User Story 3 - MCP Tools Return JSON-Safe Operational Errors (Priority: P2)

**Goal**: MCP tools return stable JSON-safe errors for storage and unexpected internal failures, with internal errors limited to `error_type` and redacted short message.

**Independent Test**: Force storage and unexpected failures through MCP tool helpers and verify structured `ok: false` payloads.

### Tests for User Story 3

- [X] T018 [US3] Add MCP tool tests in `tests/mcp_server/test_tools.py` for `sqlite3.Error` mapping to `storage_error` without raw exception details
- [X] T019 [US3] Add MCP tool tests in `tests/mcp_server/test_tools.py` for unexpected internal errors returning `internal_error`, stable `error_type`, redacted short message, and no raw secret-like values

### Implementation for User Story 3

- [X] T020 [US3] Update `_safe` in `src/work_feed_mcp/mcp_server/tools.py` to catch SQLite/storage failures and return `storage_error` JSON payloads
- [X] T021 [US3] Update `_safe` in `src/work_feed_mcp/mcp_server/tools.py` to catch unexpected internal exceptions and return `internal_error` with stable `error_type` and redacted short message
- [X] T022 [US3] Run `uv run --extra dev pytest -q tests/mcp_server/test_tools.py tests/mcp_server/test_not_ready.py`

**Checkpoint**: User Story 3 is independently complete when MCP tool helpers do not leak unstructured exceptions for local operational failures.

---

## Phase 6: User Story 4 - Read Paths Do Not Mutate Runtime State (Priority: P3)

**Goal**: Scheduler/status read behavior reports `not_ready` JSON with specific `reason`/`details`, exits with code 2, and does not initialize or migrate SQLite schema.

**Independent Test**: Run service and CLI status reads against missing, schema-less, and unsupported databases and verify no schema mutation occurs.

### Tests for User Story 4

- [X] T023 [US4] Add service tests in `tests/services/test_scheduler_status.py` proving missing database status returns `not_ready` JSON data and does not create a database file
- [X] T024 [US4] Add service tests in `tests/services/test_scheduler_status.py` proving schema-less and unsupported-version databases return `not_ready` JSON data without initializing tables or changing schema version
- [X] T025 [P] [US4] Add CLI tests in `tests/cli/test_scheduler_status_cli.py` proving not-ready cases print parseable JSON to stdout and exit with code 2

### Implementation for User Story 4

- [X] T026 [US4] Rewrite `scheduler_status` in `src/work_feed_mcp/services/scheduler_status.py` to use non-mutating readiness checks instead of `initialize_schema`
- [X] T027 [US4] Update `scheduler-status` CLI handling in `src/work_feed_mcp/cli/scheduler_status.py` to print not-ready JSON and return exit code 2
- [X] T028 [US4] Update README operational/troubleshooting text in `README.md` for scheduler-status not-ready JSON with specific `reason`/`details`
- [X] T029 [US4] Run `uv run --extra dev pytest -q tests/services/test_scheduler_status.py tests/cli/test_scheduler_status_cli.py tests/db/test_connection_policy.py`

**Checkpoint**: User Story 4 is independently complete when status reads are diagnostic-only and do not create schema.

---

## Phase 7: Polish & Cross-Cutting Verification

**Purpose**: Ensure docs, contracts, and repository gates agree after all selected stories are implemented.

- [X] T030 [P] Update Docker/public docs contract assertions in `tests/docker/test_docs_contract.py` for worker-resilience troubleshooting and scheduler-status not-ready JSON
- [X] T031 [P] Update `specs/002-worker-runtime-stability/contracts/runtime-stability.md`, `specs/002-worker-runtime-stability/data-model.md`, and `specs/002-worker-runtime-stability/quickstart.md` if implementation details refine accepted payload fields
- [X] T032 Run `uv run --extra dev pytest -q tests/runtime tests/services tests/mcp_server tests/cli`
- [X] T033 Run `uv run --extra dev pytest -q tests/docker`
- [X] T034 Run formatting/lint/type/import/test checks with direct `uv` commands
- [X] T035 Run fixture smoke with direct CLI commands
- [X] T036 Run e2e smoke with direct CLI commands
- [X] T037 Review `git status --short` to keep unrelated working-tree deletions outside the stability implementation commit

---

## Dependencies & Execution Order

### Phase Dependencies

- **Phase 1 Setup**: No dependencies.
- **Phase 2 Foundational**: Depends on Phase 1 and blocks US3/US4.
- **Phase 3 US1**: Depends on Phase 1. Delivers MVP worker resilience.
- **Phase 4 US2**: Depends on Phase 1 and can run after or alongside US1 if `src/work_feed_mcp/runtime/worker.py` edits are coordinated.
- **Phase 5 US3**: Depends on Phase 2.
- **Phase 6 US4**: Depends on Phase 2.
- **Phase 7 Polish**: Depends on selected user stories being complete.

### User Story Dependencies

- **US1 (P1)**: MVP. No dependency on US2-US4 after setup.
- **US2 (P2)**: No functional dependency on US1, but both touch `src/work_feed_mcp/runtime/worker.py`.
- **US3 (P2)**: Depends on shared not-ready payload details from Phase 2.
- **US4 (P3)**: Depends on shared not-ready payload details from Phase 2.

### Parallel Opportunities

- T001 and T002 can run in parallel.
- T003 can run before T004, and T004 blocks T005.
- T008 can run in parallel with T006-T007 because it touches `tests/services/test_scheduled_collection.py`; coordinate its resulting service contract before T009.
- T014 can run in parallel with T013 because it touches repository tests instead of runtime tests.
- T025 can run in parallel with T023-T024 because it touches CLI tests instead of service tests.
- T030 and T031 can run in parallel after implementation.

---

## Parallel Example: User Story 1

```text
Task: "T006 Add runtime tests in tests/runtime/test_worker.py"
Task: "T008 Review and extend partial-failure assertions in tests/services/test_scheduled_collection.py"
```

## Parallel Example: User Story 2

```text
Task: "T013 Add runtime tests in tests/runtime/test_worker.py"
Task: "T014 Add repository command-status assertions in tests/repositories/test_collector_control.py"
```

## Parallel Example: User Story 4

```text
Task: "T023 Add service tests in tests/services/test_scheduler_status.py"
Task: "T025 Add CLI tests in tests/cli/test_scheduler_status_cli.py"
```

---

## Implementation Strategy

### MVP First (User Story 1 Only)

1. Complete Phase 1 setup.
2. Complete Phase 3 for scheduled worker resilience.
3. Run `uv run --extra dev pytest -q tests/runtime/test_worker.py tests/services/test_scheduled_collection.py`.
4. Stop and validate that scheduled expected operational failures no longer terminate the worker.

### Incremental Delivery

1. US1: scheduled worker survives expected operational collection failures.
2. US2: manual run command failure remains command-scoped.
3. US3: MCP tools return JSON-safe storage/internal errors.
4. US4: scheduler/status read paths do not mutate SQLite state.
5. Polish: docs contracts and full verification.

### Verification Scope

- Required narrow checks are listed inside each story checkpoint.
- Required broad checks when implementation completes: formatting/lint/type/import/test checks, fixture smoke, and e2e smoke with direct `uv`/CLI commands.
- Optional coverage check: direct pytest coverage gate.
- Out of scope: live upstream collection as a required gate.

## Notes

- Keep proxy/network policy unchanged in this feature.
- Do not add source-adapter abstractions for Fiverr in this feature.
- Do not change SQLite schema or `SCHEMA_VERSION` unless implementation proves the no-migration decision wrong and the plan is updated first.
- Do not include unrelated `docs/portfolio` or other pre-existing working-tree deletions in this feature work.
