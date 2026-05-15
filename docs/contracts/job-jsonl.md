# Job JSONL contract

This document defines the normalized job JSONL contract produced by `src/upwork_app/integrations/upwork`. Downstream code must consume this contract, not Upwork transport internals.

## Producer and consumer

- Producer: `src/upwork_app/integrations/upwork` and `upwork-app-collect`
- Output: one JSON object per line when using CLI JSONL output
- Consumer: `src/upwork_app/services/ingestion`

The Upwork integration layer does not own durable state or SQLite. Ingestion adds collection-time metadata and persists records to SQLite.

Live visitor GraphQL responses may include nested `jobTile.job` fields, `ontologySkills.prefLabel`, and numeric budget values encoded as strings. The collector normalizes those response-shape details into this JSONL contract; downstream code should not consume scraper-specific SQLite rows, raw GraphQL envelopes, or live snapshots.

## Required fields

```json
{
  "source": "upwork",
  "id": "string",
  "title": "string",
  "description": "string",
  "url": "string",
  "skills": ["string"]
}
```

## Optional or nullable fields

```json
{
  "posted_at": "ISO-8601 string or null",
  "job_type": "string or null",
  "contractor_tier": "string or null",
  "hourly_min": "number or null",
  "hourly_max": "number or null",
  "fixed_amount": "number or null",
  "raw_id": "string or null"
}
```

## Current downstream behavior

`src/upwork_app/services/ingestion` validates collector JSONL/job objects and inserts only jobs whose `job_id` is not already present. Existing jobs are skipped rather than updated for observation history.

The jobs store adds these DB-managed fields:

- `content_hash`
- `first_seen_at`
- `created_at`

The app does not persist per-job observation logs or raw normalized payload archives. Scheduled collection may persist redacted operational run summaries separately from this JSONL contract.

## Client fields

The current collector contract has no rich client fields.

Therefore `src/upwork_app/repositories/client_analytics.py` aggregates client-related dimensions only when those columns exist in SQLite `jobs`. Missing dimensions return `unknown`/`null`; the app must not infer client country/spend/payment status from title or description text.

## Future additions

Future ranking/reporting features may add `score`, `score_version`, `score_reasons`, presentation summaries, or action hints downstream. These are not collector JSONL required fields.
