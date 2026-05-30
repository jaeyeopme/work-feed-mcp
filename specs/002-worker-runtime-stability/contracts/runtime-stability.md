# Contract: Worker Runtime Stability

## Scheduled Worker Failure

When automatic scheduled collection fails with an expected operational
collection failure:

```json
{
  "worker": "continues",
  "run": {
    "status": "failed",
    "error_type": "UpstreamBlockedError",
    "redacted_error": "blocked token=<redacted>"
  }
}
```

Contract requirements:

- The worker process continues after the failure.
- `collector_runs` contains the failed run.
- `collector_run_results` contains any successful query slices completed before
  the failure and the failed query slice.
- Error text is redacted before persistence.
- Later commands can still be processed.
- Non-collector validation/ingestion failures are considered expected only when
  the scheduled collection service has already recorded a failed run/result for
  them.
- Unexpected internal programming errors outside the expected collection failure
  path are not silently swallowed.

## Manual Run Command Failure

When `collector_run_once` is queued and collection fails:

```json
{
  "ok": true,
  "command": {
    "command_id": "cmd-1",
    "command_type": "run_once",
    "status": "failed",
    "error_type": "UpstreamBlockedError",
    "redacted_error": "blocked token=<redacted>"
  }
}
```

Contract requirements:

- The command reaches terminal `failed`.
- The worker remains alive.
- Later commands can transition normally.
- A queued `run_once` command can fail safely while the worker is paused without
  converting the paused scheduled state into an automatic run.
- Failure details are redacted.

## MCP Operational Error Payloads

MCP tools return JSON-safe errors for bounded operational failures.

Not ready:

```json
{
  "ok": false,
  "error": "not_ready",
  "reason": "db_missing",
  "details": "database file does not exist",
  "next_action": "start work-feed-worker"
}
```

Invalid request:

```json
{
  "ok": false,
  "error": "invalid_request",
  "message": "limit must be a positive integer"
}
```

Storage failure:

```json
{
  "ok": false,
  "error": "storage_error",
  "message": "runtime storage unavailable"
}
```

Unexpected internal failure:

```json
{
  "ok": false,
  "error": "internal_error",
  "error_type": "RuntimeError",
  "message": "unexpected runtime failure"
}
```

Contract requirements:

- All error payloads are JSON-safe.
- Storage/internal errors must not expose raw exception text when it could
  contain credentials, paths with secrets, upstream payloads, or environment
  material.
- Internal errors include a stable `error_type` and redacted short message, not
  full raw exception details.
- Not-ready reasons remain `db_missing`, `schema_missing`, or
  `unsupported_schema`.
- Not-ready payloads include safe `details` text for the reason.

## Status Read Path

When scheduler/status is requested against a missing or uninitialized database:

```json
{
  "ok": false,
  "error": "not_ready",
  "reason": "db_missing",
  "details": "database file does not exist",
  "next_action": "start work-feed-worker"
}
```

Contract requirements:

- Missing database reads do not create a database file.
- Schema-less database reads do not initialize runtime tables.
- Unsupported future schema reads do not downgrade or mutate the database.
- CLI exits with code 2 for not-ready cases while keeping stdout parseable JSON.
