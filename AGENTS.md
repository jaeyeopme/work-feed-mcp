# AGENTS.md — upwork monorepo

## Role and intent

This repository is the monorepo for the Upwork job discovery pipeline. Keep modules separated by pipeline responsibility:

- `packages/collector`: Upwork collection and normalized JSONL stdout.
- `packages/ingest`: JSONL ingestion into SQLite plus collected_at/query/run/raw-record metadata.
- `packages/analytics`: SQLite-backed statistics queries and report-ready data.
- `packages/ranker`: future Jaeyeop-specific application value scoring.
- `packages/report`: future Discord/Markdown/HTML rendering.

The currently implemented MVP path is `collector → ingest → analytics`.

## Boundaries

Do not move downstream responsibilities into `collector`. Collector must stay a dumb, secret-safe JSONL producer:

- stdout: job JSONL records only.
- stderr: diagnostics only, with credential/session/proxy/token redaction.
- no default durable local state, SQLite, snapshots, ranking, analytics, scheduling, notifications, or UI.
- no proxy acquisition docs or access-control bypass playbooks.

`ingest` owns SQLite persistence and raw normalized collector-record provenance. `analytics` owns SQLite-only queries. Ranking, application decisions, auto-apply, message generation, and report delivery stay out of the MVP.

Use `packages/collector/AGENTS.md`, `packages/collector/docs/PRD.md`, `packages/collector/docs/TEST_PLAN.md`, and `packages/collector/docs/adr/0001-python-jsonl-collector.md` for collector-specific decisions.

## Verification

For collector changes, run from repo root:

```bash
make quality
make smoke
```

For ingest changes:

```bash
cd packages/ingest
ruff format --check .
ruff check .
mypy src
pytest -q
make smoke
```

For analytics changes:

```bash
cd packages/analytics
ruff format --check .
ruff check .
mypy src
pytest -q
```

For live evidence, run only with explicit opt-in:

```bash
make live-smoke QUERY="python"
```

Report live status separately from fixture/local contract evidence.
