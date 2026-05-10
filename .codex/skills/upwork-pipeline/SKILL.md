---
name: upwork-pipeline
description: Work safely in this Upwork job data pipeline repository. Use when Codex needs to inspect, modify, test, document, or plan changes for the repo's collector, ingest, analytics, future ranker, or future report modules; when preserving collector/ingest/analytics boundaries matters; or when running local fixture/SQLite verification for this project.
---

# Upwork Pipeline

Use this project-local skill for work in `/Users/jaeyeop/Workspace/upwork`.

## First read

For repo orientation, read only what the task needs:

- `docs/LLM_CONTEXT.md` — fastest current-state overview.
- `docs/EXTERNAL_LLM_GUIDE.md` — prompts/context for outside LLMs.
- `docs/contracts/job-jsonl.md` — collector stdout contract.
- `packages/<module>/README.md` — package-specific CLI and scope.
- `packages/collector/AGENTS.md` — collector-specific hard boundaries.

## Current implementation

Implemented MVP:

```text
packages/collector -> JSONL stdout
packages/ingest    -> SQLite persistence
packages/analytics -> SQLite-only queries
```

Not implemented:

- `packages/ranker` — future scoring/ranking.
- `packages/report` — future rendering/report delivery.

## Hard boundaries

- Keep `collector` a dumb, secret-safe JSONL producer.
- Do not add SQLite, snapshots, analytics, ranking, reporting, scheduling, notifications, or UI to `collector`.
- Put JSONL validation and SQLite writes in `ingest`.
- Make `analytics` read SQLite only. Do not make it call collector or parse JSONL directly.
- Do not infer missing client fields from title/description. Return `unknown`/`null` when absent.
- Keep LLM ranking, auto-apply, proposal/message generation, and report delivery out of MVP unless explicitly requested as future `ranker`/`report` work.

## Common task routing

| User asks | Work in |
|---|---|
| collection, JSONL schema, Upwork response normalization | `packages/collector` |
| SQLite schema, JSONL ingestion, run metadata, raw record provenance | `packages/ingest` |
| summary/skills/jobs/budgets/runs/clients queries | `packages/analytics` |
| scoring/ranking/application value | future `packages/ranker` only |
| Discord/Markdown/HTML output | future `packages/report` only |
| external LLM handoff docs | `docs/EXTERNAL_LLM_GUIDE.md`, `docs/LLM_CONTEXT.md` |

## Verification

Run the smallest relevant set, then expand when boundaries are touched.

Collector:

```bash
make quality
make smoke
```

Ingest:

```bash
cd packages/ingest
ruff format --check .
ruff check .
mypy src
pytest -q
make smoke
```

Analytics:

```bash
cd packages/analytics
ruff format --check .
ruff check .
mypy src
pytest -q
```

Local E2E:

```bash
rm -f /tmp/upwork-e2e.sqlite
PYTHONPATH=packages/collector/src python -m upwork_collector collect \
  --fixture packages/collector/tests/fixtures/visitor_job_search_response.json \
  | PYTHONPATH=packages/ingest/src python -m upwork_ingest ingest \
      --db /tmp/upwork-e2e.sqlite \
      --input - \
      --query python
PYTHONPATH=packages/analytics/src python -m upwork_analytics query summary --db /tmp/upwork-e2e.sqlite
PYTHONPATH=packages/analytics/src python -m upwork_analytics query skills --db /tmp/upwork-e2e.sqlite
PYTHONPATH=packages/analytics/src python -m upwork_analytics query clients --db /tmp/upwork-e2e.sqlite
```

Live smoke requires explicit opt-in:

```bash
make live-smoke QUERY="python"
```

Report live evidence separately from fixture/local contract evidence.

## Before final answer

Report:

- changed files or read-only finding scope
- verification commands and PASS/FAIL
- whether live smoke was not run
- any boundary risk, especially collector persistence or fake client enrichment

## Reference

If the task needs compact handoff language or external prompt wording, read `references/external-llm-brief.md`.
