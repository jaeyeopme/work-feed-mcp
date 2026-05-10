# Job JSONL contract

이 문서는 `src/upwork_app/integrations/upwork`가 생산하는 normalized job JSONL contract입니다. Downstream code는 Upwork transport internals가 아니라 이 contract를 소비해야 합니다.

## Producer and consumer

- Producer: `src/upwork_app/integrations/upwork` and `upwork-app-collect`
- Output: one JSON object per line when using CLI JSONL output
- Consumer: `src/upwork_app/services/ingestion`

The Upwork integration layer does not own durable state or SQLite. Ingestion adds collection-time metadata and persists records to SQLite.

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

`src/upwork_app/services/ingestion` validates collector JSONL and adds these SQLite fields/metadata:

- `run_id`
- `source_query`
- `content_hash`
- `first_seen_at`
- `last_seen_at`
- `observed_at`
- `received_at`
- `payload_json` in `raw_records`

`payload_json` is the normalized JSON object emitted by the collector/integration layer. It is not an upstream GraphQL/private payload.

## Client fields

The current collector contract has no rich client fields.

Therefore `src/upwork_app/repositories/client_analytics.py` aggregates client-related dimensions only when those columns exist in SQLite `jobs`. Missing dimensions return `unknown`/`null`; the app must not infer client country/spend/payment status from title or description text.

## Future additions

Future ranking/reporting features may add `score`, `score_version`, `score_reasons`, presentation summaries, or action hints downstream. These are not collector JSONL required fields.
