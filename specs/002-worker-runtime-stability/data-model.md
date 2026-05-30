# Data Model: Worker Runtime Stability

## Collector Run

Represents one scheduled or manual collection attempt.

Fields already present:

- `run_id`: stable run identifier.
- `started_at`: run start time.
- `finished_at`: run finish time, nullable while running.
- `status`: `running`, `success`, or `failed`.
- `trigger`: `worker_interval`, `mcp_run_once`, or other existing trigger names.
- `query_count`: number of query slices attempted/planned.
- `total_seen`: total observed records from successful query slices.
- `total_inserted`: total newly stored records from successful query slices.
- `total_skipped`: total duplicate records skipped from successful query slices.
- `error_type`: failure class name for failed runs.
- `redacted_error`: bounded diagnostic message with credential-like values redacted.

Validation rules:

- Failed scheduled runs must have `status = failed`, `finished_at`, `error_type`,
  and `redacted_error`.
- Successful query slices completed before a later failure remain reflected in
  totals.
- Validation/ingestion failures are worker-swallowable only when the scheduled
  collection service has recorded the failed run/result before re-raising.
- Redacted error text must not contain token, cookie, session, proxy credential,
  authorization header, or raw upstream payload material.

## Collector Run Result

Represents one query slice within a collector run.

Fields already present:

- `run_id`: parent collector run.
- `query`: query text or null for the unfiltered/default run.
- `status`: `success` or `failed`.
- `attempts`: collection attempts for the query slice.
- `seen_count`: observed record count for successful slices.
- `inserted_count`: newly stored unique record count for successful slices.
- `skipped_count`: duplicate skipped count for successful slices.
- `error_type`: failure class name for failed slices.
- `redacted_error`: bounded redacted diagnostic text for failed slices.
- `started_at`, `finished_at`: slice timing.

Validation rules:

- A failed query slice records zero counts for that failed slice.
- Previously successful slices remain committed.
- Retry attempt counts reflect existing retry policy.

## Collector Command

Represents one queued MCP control command.

Fields already present:

- `command_id`: stable command identifier.
- `command_type`: `run_once`, `pause`, `resume`, or `update_config`.
- `payload`: command input.
- `status`: `queued`, `running`, `applied`, or `failed`.
- `created_at`, `started_at`, `finished_at`: command timing.
- `requested_by`: requester label.
- `result`: JSON-safe applied result.
- `error_type`: failure class name for failed commands.
- `redacted_error`: bounded redacted diagnostic text for failed commands.

State transitions:

```text
queued -> running -> applied
queued -> running -> failed
```

Validation rules:

- `collector_run_once` collection failure transitions the command to `failed`.
- A failed command does not stop the worker from processing later commands.
- Error text is redacted before persistence.

## MCP Error Payload

Represents an agent-facing operational error.

Fields:

- `ok`: always `false`.
- `error`: stable category such as `not_ready`, `invalid_request`,
  `storage_error`, or `internal_error`.
- `error_type`: stable exception/category name for internal errors when useful.
- `message`: bounded redacted short diagnostic text when safe and useful.
- `reason`: stable not-ready reason when available.
- `details`: required safe context for `not_ready`; optional safe context for
  storage/internal errors when useful.
- `next_action`: operator-oriented remediation hint when available.

Validation rules:

- Payload must be JSON-safe.
- Payload must not expose credential-like values or raw upstream payloads.
- Internal errors must not expose full raw exception details.
- Invalid user input remains distinguishable from storage/runtime failure.

## Runtime Database Readiness

Represents the state read/control paths observe before returning status or data.

States:

- `db_missing`: database file does not exist.
- `schema_missing`: database exists but required runtime tables are absent.
- `unsupported_schema`: database schema version is newer than supported.
- `ready`: database and required runtime tables are available.

Validation rules:

- Read/status paths do not create or migrate schema.
- Worker write paths remain responsible for initialization.
- Existing `not_ready` behavior remains stable for MCP tools.
- Scheduler/status read commands return parseable `not_ready` JSON with
  specific `reason` and `details` fields and exit with code 2.
