# Job JSONL contract

이 문서는 `packages/collector`가 stdout으로 출력하는 normalized job JSONL contract입니다. Downstream package는 collector internals가 아니라 이 contract를 소비해야 합니다.

## Producer

- Producer: `packages/collector`
- Output: stdout, one JSON object per line
- Consumer: `packages/ingest`

Collector는 durable state나 SQLite를 쓰지 않습니다. `ingest`가 수집 시점 metadata와 SQLite 저장을 담당합니다.

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

`packages/ingest`는 위 collector JSONL을 검증한 뒤 SQLite에 다음 정보를 추가합니다.

- `run_id`
- `source_query`
- `content_hash`
- `first_seen_at`
- `last_seen_at`
- `observed_at`
- `received_at`
- `payload_json` in `raw_records`

`payload_json`은 collector-emitted normalized JSON object입니다. upstream GraphQL/private payload가 아닙니다.

## Client fields

현재 collector contract에는 rich client fields가 없습니다.

따라서 `packages/analytics`는 client-related column이 SQLite `jobs` table에 있을 때만 해당 dimension을 집계합니다. 없으면 `unknown`/`null`로 반환하고, title/description에서 추론하지 않습니다.

## Future downstream additions

- `packages/ranker` may add `score`, `score_version`, `score_reasons`, `reject_reasons` later.
- `packages/report` may add presentation-only sections, badges, summaries, and action hints later.

이 future field들은 collector JSONL required field가 아닙니다.
