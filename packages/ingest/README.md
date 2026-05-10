# upwork-ingest

`upwork-ingest` reads normalized collector JSONL from a file or stdin and writes a local SQLite database.

It owns persistence only: JSONL parsing, collector-contract validation, SQLite schema creation, run metadata, job upserts, skills, observations, and raw normalized record provenance. It does not call Upwork, invoke the collector, rank jobs, render reports, or fabricate client analytics.

## CLI

```bash
upwork-ingest ingest --db .local/upwork.sqlite --input jobs.jsonl --query "python"
cat jobs.jsonl | upwork-ingest ingest --db .local/upwork.sqlite --input - --query "python"
```

Optional `--run-id` accepts an externally assigned run id. Without it, a UUID-based run id is generated.

`raw_records.payload_json` stores a canonical JSON representation of the collector-emitted normalized JSON object. `content_hash` is a deterministic SHA-256 hash of that canonical payload.
