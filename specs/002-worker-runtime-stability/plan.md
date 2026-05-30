# Implementation Plan: Worker Runtime Stability

**Branch**: `002-worker-runtime-stability` | **Date**: 2026-05-30 | **Spec**: [spec.md](./spec.md)

**Input**: Feature specification from `specs/002-worker-runtime-stability/spec.md`

## Summary

Stabilize the local Docker/MCP runtime before adding new source adapters. The
worker must survive expected upstream collection failures, manual collection
commands must fail audibly without killing the worker, MCP tools must return
stable JSON-safe operational errors, and status/read paths must respect
worker-owned SQLite initialization.

The approach keeps the current architecture: `runtime` owns the long-running
loop, `services` own orchestration and readiness/error mapping, `repositories`
own SQLite state changes, `mcp_server` wraps service calls into JSON-safe tool
payloads, and `cli` exposes local diagnostics without becoming the primary user
interface.

## Technical Context

**Language/Version**: Python >=3.11; Docker runtime image currently Python 3.13

**Primary Dependencies**: `curl-cffi`, `mcp`, Python SQLite standard library

**Storage**: SQLite at `WORK_FEED_DB`; Docker Compose volume for normal runtime

**Testing**: pytest, ruff, mypy, import-linter, fixture smoke, e2e smoke

**Target Platform**: Docker Compose services plus local CLI/MCP clients

**Project Type**: Docker/MCP-first Python data engine with local/debug CLI

**Performance Goals**: Scheduled failure handling must add no meaningful latency
outside failure paths; command polling remains bounded by existing sleep/poll
intervals; MCP error wrapping must not perform extra writes from read paths.

**Constraints**: Secret-safe diagnostics; no raw upstream private payload
persistence; live collection is explicit opt-in evidence; worker owns schema and
writes; MCP read/control paths do not initialize schema; control remains
enqueue-only; scheduled runs continue only after expected operational collection
failures, not arbitrary internal programming errors. Validation/ingestion
failures are worker-swallowable only when they come from the scheduled collection
service after that service has recorded failed run history.

**Scale/Scope**: Personal/local job-discovery data engine; one worker, one MCP
server, one SQLite runtime database; source adapter expansion is out of scope.

## Constitution Check

*GATE: Must pass before Phase 0 research. Re-check after Phase 1 design.*

- Scope gate: PASS. Runtime stability is within Docker/MCP data-engine
  responsibilities and does not add UI, ranking, proposal generation, or new
  source adapters.
- Secret-safety gate: PASS. The plan requires redaction for run history,
  command failures, MCP error payloads, and diagnostics.
- Layer gate: PASS. Changes stay in `runtime`, `services`, `repositories`,
  `mcp_server`, `cli`, and tests. No import-linter boundary change is planned.
- SQLite authority gate: PASS. The plan strengthens worker-owned schema
  initialization and read-path non-mutation.
- Verification gate: PASS. Narrow tests and full repository gates are listed in
  quickstart and success criteria. Live collection remains out of normal
  verification.

## Project Structure

### Documentation (this feature)

```text
specs/002-worker-runtime-stability/
├── plan.md
├── research.md
├── data-model.md
├── quickstart.md
├── contracts/
│   └── runtime-stability.md
└── tasks.md              # Created later by speckit-tasks
```

### Source Code (repository root)

```text
src/work_feed_mcp/
├── runtime/
│   └── worker.py                 # Worker loop and command failure behavior
├── services/
│   ├── collector_control.py      # Runtime readiness and control services
│   ├── health.py                 # Runtime readiness checks
│   ├── job_queries.py            # MCP-safe read services
│   ├── run_status.py             # Run/status read services
│   ├── scheduled_collection.py   # Collection-owned failure recording
│   └── scheduler_status.py       # CLI status read policy
├── repositories/
│   ├── collector_control.py      # Command state transitions
│   └── run_history.py            # Run/result history state
├── mcp_server/
│   └── tools.py                  # JSON-safe MCP tool wrappers
├── cli/
│   └── scheduler_status.py       # CLI status output and exit behavior
└── db/
    └── connection.py             # Read/write connection policy, if needed

tests/
├── repositories/test_collector_control.py
├── db/test_connection_policy.py
├── runtime/test_worker.py
├── services/test_scheduled_collection.py
├── services/test_scheduler_status.py
├── mcp_server/test_tools.py
├── mcp_server/test_not_ready.py
├── cli/test_scheduler_status_cli.py
└── docker/test_docs_contract.py
```

**Structure Decision**: Use the existing package and ownership boundaries. Add
small helper functions only where they reduce repeated error/redaction mapping
across MCP or worker runtime paths.

## Phase 0 Research

See [research.md](./research.md).

## Phase 1 Design

See [data-model.md](./data-model.md), [contracts/runtime-stability.md](./contracts/runtime-stability.md), and [quickstart.md](./quickstart.md).

## Post-Design Constitution Check

- Scope gate: PASS. The design does not expand product scope.
- Secret-safety gate: PASS. Error payloads and persisted failure details require
  redaction.
- Layer gate: PASS. Contracts map cleanly onto existing layers.
- SQLite authority gate: PASS. Scheduler/status read behavior is explicitly
  aligned with non-mutating read paths.
- Verification gate: PASS. The quickstart lists narrow and broad checks, with
  no live upstream requirement.

## Complexity Tracking

No constitution violations. No additional projects, external dependencies,
schema migrations, or source adapter abstractions are planned.
