# AGENTS.md — upwork monorepo

## Role and intent

This repository is the monorepo for the Upwork job discovery pipeline. Keep modules separated by pipeline responsibility:

- `packages/collector`: Upwork collection and normalized JSONL stdout.
- `packages/ingest`: JSONL ingestion into SQLite/Postgres plus collected_at/query/snapshot metadata.
- `packages/analytics`: statistics queries and report data.
- `packages/ranker`: Jaeyeop-specific application value scoring.
- `packages/report`: Discord/Markdown/HTML rendering.

The currently implemented module is `packages/collector`.

## Boundaries

Do not move downstream responsibilities into `collector`. Collector must stay a dumb, secret-safe JSONL producer:

- stdout: job JSONL records only.
- stderr: diagnostics only, with credential/session/proxy/token redaction.
- no default durable local state, SQLite, snapshots, ranking, analytics, scheduling, notifications, or UI.
- no proxy acquisition docs or access-control bypass playbooks.

Use `packages/collector/AGENTS.md`, `packages/collector/docs/PRD.md`, `packages/collector/docs/TEST_PLAN.md`, and `packages/collector/docs/adr/0001-python-jsonl-collector.md` for collector-specific decisions.

## Verification

For collector changes, run from repo root:

```bash
make quality
make smoke
```

For live evidence, run only with explicit opt-in:

```bash
make live-smoke QUERY="python"
```

Report live status separately from fixture/local contract evidence.
