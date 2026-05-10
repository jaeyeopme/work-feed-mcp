# External LLM Guide: using the Upwork backend

이 문서는 ChatGPT, Claude, Gemini 같은 외부 LLM에게 이 프로젝트를 설명하고 작업을 맡길 때 붙여넣기 좋은 가이드입니다.

목표는 외부 LLM이 이 저장소를 **지원 자동화 도구**로 오해하지 않고, 현재 구현된 **수집 → SQLite 저장 → 기본 분석 → FastAPI/CLI 제공** 흐름을 올바르게 사용/확장하도록 만드는 것입니다.

## Copy-paste project brief

외부 LLM에게 먼저 아래 블록을 붙여넣으세요.

```text
You are helping with an Upwork job discovery backend.

Current app-first structure:
- src/upwork_app/main.py: FastAPI app entrypoint.
- src/upwork_app/api/routes: HTTP endpoints.
- src/upwork_app/schemas: Pydantic request/response models.
- src/upwork_app/services: collect, ingest, and analytics use cases.
- src/upwork_app/repositories: SQLite query/persistence helpers.
- src/upwork_app/db: SQLite schema/connection helpers.
- src/upwork_app/domain: collector-record validation/domain types.
- src/upwork_app/integrations/upwork: Upwork transport, credentials, GraphQL, normalization.
- src/upwork_app/cli: local batch CLIs.

Legacy packages remain for compatibility:
- packages/collector: legacy Upwork/fixture JSONL producer.
- packages/ingest: legacy JSONL-to-SQLite ingest.
- packages/analytics: legacy SQLite analytics.

Product intent:
- Stable, analysis-ready data collection.
- Not Upwork application automation.
- No auto-apply, proposal/message generation, LLM ranking, scheduler, or report delivery in MVP.

Hard boundaries:
- Keep Upwork collection dumb and secret-safe.
- Store only normalized collector job records, not upstream GraphQL/private payloads.
- SQLite persistence belongs in ingestion/db/repository layers.
- Analytics reads SQLite only.
- Client analytics must not infer missing client fields from title/description. If client columns are absent, return unknown/null.

Use these docs as source of truth:
- README.md
- docs/LLM_CONTEXT.md
- docs/fastapi-backend-structure.md
- docs/contracts/job-jsonl.md
- packages/collector/AGENTS.md for legacy collector-specific constraints
```

## What the current project can do

The project can run this local flow:

```text
fixture or live collector input
  -> normalized job records/JSONL
  -> SQLite database
  -> basic JSON analytics queries
  -> FastAPI or CLI responses
```

Local fixture E2E example:

```bash
uv run --extra dev upwork-app-collect \
  --fixture packages/collector/tests/fixtures/visitor_job_search_response.json \
  > /tmp/upwork-e2e.jsonl

uv run --extra dev upwork-app-ingest \
  --db /tmp/upwork-e2e.sqlite \
  --input /tmp/upwork-e2e.jsonl \
  --query python

uv run --extra dev upwork-app-analytics summary --db /tmp/upwork-e2e.sqlite
uv run --extra dev upwork-app-analytics skills --db /tmp/upwork-e2e.sqlite
uv run --extra dev upwork-app-analytics clients --db /tmp/upwork-e2e.sqlite
```

FastAPI example:

```bash
uv run --extra dev uvicorn upwork_app.main:app --reload
```

Then call:

```text
GET  /health
POST /collect
POST /ingest
POST /collect-and-ingest
GET  /analytics/summary
```

## Module map for external LLMs

| Module/path | Status | Use it for | Do not use it for |
|---|---|---|---|
| `src/upwork_app/api/routes` | implemented | HTTP request/response binding | business logic or DB internals |
| `src/upwork_app/services` | implemented | use-case orchestration | framework-specific HTTP details |
| `src/upwork_app/repositories`, `src/upwork_app/db` | implemented | SQLite reads/writes/schema | Upwork HTTP calls |
| `src/upwork_app/integrations/upwork` | implemented | Upwork/fixture transport and normalization | SQLite, analytics, ranking, reporting |
| `packages/collector`, `packages/ingest`, `packages/analytics` | legacy-compatible | existing package tests/compatibility | new app-first features unless maintaining legacy |
| `packages/ranker`, `packages/report` | not implemented | future scoring/reporting placeholders | current MVP tasks |

## Verification commands to give external LLMs

App-first changes:

```bash
make app-quality
make app-smoke
make e2e-smoke
```

Full compatibility check:

```bash
make quality
make smoke
```

Live smoke is explicit opt-in only:

```bash
make live-smoke QUERY="python"
```

Live evidence must be reported separately from fixture/local contract evidence.

## Common wrong assumptions to correct

- “The project auto-applies to jobs.” Wrong. Auto-apply/message generation is out of scope.
- “The project ranks jobs.” Wrong. Ranker is not implemented.
- “Analytics can infer client spend/country from text.” Wrong. Missing client fields become unknown/null.
- “Fixture tests prove live Upwork works.” Wrong. Fixture/local tests prove contracts only; live smoke is separate opt-in evidence.
- “New code should go under `packages/*`.” Usually wrong. New backend code should go under `src/upwork_app` unless explicitly maintaining legacy compatibility.

## Minimal context bundle to attach

1. `README.md`
2. `docs/LLM_CONTEXT.md`
3. `docs/fastapi-backend-structure.md`
4. `docs/EXTERNAL_LLM_GUIDE.md`
5. `docs/contracts/job-jsonl.md`
6. Relevant source/tests under `src/upwork_app`.
7. Legacy package docs/tests only when the task touches compatibility behavior.

Do not paste `.omx/logs`, `.omx/state`, or runtime traces unless the question is specifically about OMX execution.
