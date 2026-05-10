# External LLM Guide: using the Upwork data pipeline

이 문서는 ChatGPT, Claude, Gemini 같은 외부 LLM에게 이 프로젝트를 설명하고 작업을 맡길 때 붙여넣기 좋은 가이드입니다.

목표는 외부 LLM이 이 저장소를 **지원 자동화 도구**로 오해하지 않고, 현재 구현된 **데이터 수집 → SQLite 저장 → 기본 분석** 파이프라인을 올바르게 사용/확장하도록 만드는 것입니다.

## Copy-paste project brief

외부 LLM에게 먼저 아래 블록을 붙여넣으세요.

```text
You are helping with an Upwork job data pipeline monorepo.

Current implemented MVP:
- packages/collector: collects Upwork/fixture data and emits normalized job JSONL to stdout.
- packages/ingest: reads collector JSONL from file/stdin, validates the contract, and writes SQLite.
- packages/analytics: reads SQLite only and returns basic query results as JSON.

Not implemented:
- packages/ranker: future scoring/ranking, not part of current MVP.
- packages/report: future Discord/Markdown/HTML rendering, not part of current MVP.

Product intent:
- Stable, analysis-ready data collection.
- Not Upwork application automation.
- No auto-apply, proposal/message generation, LLM ranking, or report delivery in MVP.

Hard boundaries:
- Never add SQLite/storage/analytics/ranking/reporting to packages/collector.
- Collector stdout must contain job JSONL records only.
- Ingest owns SQLite persistence and raw normalized collector-record provenance.
- Analytics reads SQLite only; it must not call collector or parse JSONL directly.
- Client analytics must not infer missing client fields from title/description. If client columns are absent, return unknown/null.

Use these docs as source of truth:
- docs/LLM_CONTEXT.md
- README.md
- docs/contracts/job-jsonl.md
- packages/collector/AGENTS.md
- packages/*/README.md
- source and tests under packages/*
```

## What the current project can do

The project can run this local flow:

```text
fixture or live collector input
  -> normalized job JSONL
  -> SQLite database
  -> basic JSON analytics queries
```

Local fixture E2E example:

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

Expected interpretation:

- `summary` proves rows were stored in SQLite.
- `skills` proves normalized skill aggregation works.
- `clients` should usually return unavailable/unknown buckets because the current collector contract has no rich client fields.

## Module map for external LLMs

| Module | Status | Use it for | Do not use it for |
|---|---|---|---|
| `packages/collector` | implemented | Upwork/fixture collection, normalization, JSONL stdout | SQLite, analytics, ranking, reporting, scheduling |
| `packages/ingest` | implemented | JSONL validation, SQLite schema/storage, run/job/skill/raw provenance | Upwork calls, collector invocation, ranking/reporting |
| `packages/analytics` | implemented | SQLite-only summary/skills/jobs/budgets/runs/clients queries | JSONL parsing, collector calls, DB mutation, ranking |
| `packages/ranker` | not implemented | future LLM/application value scoring | current MVP tasks |
| `packages/report` | not implemented | future Discord/Markdown/HTML rendering | current MVP tasks |

## Useful prompts for external LLMs

### Ask for a codebase explanation

```text
Using docs/LLM_CONTEXT.md and the package READMEs, explain the current Upwork pipeline architecture. Keep collector, ingest, analytics, ranker, and report boundaries separate. Do not assume ranker/report are implemented.
```

### Ask for a safe feature plan

```text
Plan a change for this repo. Preserve these boundaries:
- collector remains JSONL-only stdout and no SQLite.
- ingest owns SQLite persistence.
- analytics reads SQLite only.
- ranker/report are not implemented unless explicitly requested.
Return impacted files, tests to add/update, and verification commands.
```

### Ask for debugging help

```text
Debug this failure in the Upwork data pipeline. First identify which module owns the behavior: collector, ingest, or analytics. Do not move responsibilities across module boundaries. Use source/tests as evidence and propose the smallest fix.

Failure/log:
<PASTE ERROR>
```

### Ask for a query/analysis usage answer

```text
Given the current implementation, show how to collect fixture data into SQLite and run analytics queries. Use PYTHONPATH commands from docs/LLM_CONTEXT.md. Explain what summary, skills, budgets, runs, and clients mean. Do not mention ranker/report as available commands.
```

### Ask for future ranker/report design

```text
Design a future extension for packages/ranker or packages/report. Treat them as unimplemented placeholders. The design must consume SQLite/analytics outputs and must not require collector to store state or make ranking decisions.
```

## Verification commands to give external LLMs

When an external LLM proposes or changes code, require it to report which commands it ran.

Collector changes:

```bash
make quality
make smoke
```

Ingest changes:

```bash
cd packages/ingest
ruff format --check .
ruff check .
mypy src
pytest -q
make smoke
```

Analytics changes:

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

Live smoke is explicit opt-in only:

```bash
make live-smoke QUERY="python"
```

Live evidence must be reported separately from fixture/local contract evidence.

## Common wrong assumptions to correct

If an external LLM says any of these, correct it:

- “The collector stores jobs in SQLite.” Wrong. Ingest stores SQLite.
- “The project ranks jobs.” Wrong. Ranker is not implemented.
- “The project generates applications/proposals.” Wrong. Auto-apply/message generation is out of scope.
- “Analytics can infer client spend/country from text.” Wrong. Missing client fields become unknown/null.
- “Report output is available.” Wrong. Report package is not implemented.
- “Fixture tests prove live Upwork works.” Wrong. Fixture/local tests prove contracts only; live smoke is separate opt-in evidence.

## Minimal context bundle to attach

When asking an external LLM for serious work, attach or paste these files:

1. `docs/LLM_CONTEXT.md`
2. `docs/EXTERNAL_LLM_GUIDE.md`
3. `docs/contracts/job-jsonl.md`
4. `README.md`
5. Relevant package README:
   - `packages/collector/README.md`
   - `packages/ingest/README.md`
   - `packages/analytics/README.md`
6. Relevant tests for the package being changed.

Do not paste `.omx/logs`, `.omx/state`, or runtime traces unless the question is specifically about OMX execution.
