# Job JSONL contract

`packages/collector` emits one normalized Upwork job object per stdout line.

Required fields:

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

Optional or nullable fields:

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

Downstream modules may add fields but must not require collector to store durable state.

Planned downstream additions:

- ingest: `collected_at`, `query`, `run_id`, `snapshot_id`, `content_hash`, `first_seen_at`, `last_seen_at`.
- ranker: `score`, `score_version`, `score_reasons`, `reject_reasons`.
- report: presentation-only sections, badges, summaries, and action hints.
