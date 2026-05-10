# External LLM brief

Use this when the user wants to hand this repo to another LLM.

```text
This is an Upwork job data pipeline repo.

Implemented:
- collector: Upwork/fixture -> normalized job JSONL stdout
- ingest: collector JSONL -> SQLite
- analytics: SQLite-only basic queries

Not implemented:
- ranker: future scoring/ranking
- report: future rendering

Hard rules:
- Do not add SQLite/storage/analytics/ranking/reporting to collector.
- Ingest owns SQLite persistence.
- Analytics reads SQLite only.
- Missing client fields must be unknown/null, not inferred from text.
- No auto-apply, proposal generation, or LLM ranking in MVP.

Read docs/LLM_CONTEXT.md, docs/contracts/job-jsonl.md, README.md, and the relevant package README before changing code.
```
