# External LLM Guide: using the Upwork backend

이 문서는 ChatGPT, Claude, Gemini 같은 외부 LLM에게 이 프로젝트를 설명하고 작업을 맡길 때 붙여넣기 좋은 가이드입니다.

목표는 외부 LLM이 이 저장소를 **지원 자동화 도구**로 오해하지 않고, 현재 구현된 **수집 → SQLite 저장 → 기본 분석 → FastAPI/CLI 제공** 흐름을 올바르게 사용/확장하도록 만드는 것입니다.

## Copy-paste project brief

```text
You are helping with an Upwork job discovery backend.

Current structure:
- src/upwork_app/main.py: FastAPI app entrypoint.
- src/upwork_app/api/routes: HTTP endpoints.
- src/upwork_app/schemas: Pydantic request/response models.
- src/upwork_app/services: collect, ingest, and analytics use cases.
- src/upwork_app/repositories: SQLite query/persistence helpers.
- src/upwork_app/db: SQLite schema/connection helpers.
- src/upwork_app/domain: collector-record validation/domain types.
- src/upwork_app/integrations/upwork: Upwork transport, credentials, GraphQL, normalization.
- src/upwork_app/cli: local batch CLIs.
- tests: app-level tests and fixtures.

Product intent:
- Stable, deduplicated job storage for later external LLM selection.
- Not Upwork application automation.
- No auto-apply, proposal/message generation, LLM ranking, scheduler, or report delivery in MVP.

Hard boundaries:
- Keep Upwork collection dumb and secret-safe.
- Store only deduplicated jobs and job skills, not upstream GraphQL/private payloads, run history, or observation logs.
- SQLite persistence belongs in ingestion/db/repository layers.
- Analytics reads SQLite only.
- HTTP endpoints use server-side DB settings and must not accept arbitrary caller-selected DB paths.
- Client analytics must not infer missing client fields from title/description. If client columns are absent, return unknown/null.

Use these docs as source of truth:
- README.md
- docs/LLM_CONTEXT.md
- docs/fastapi-backend-structure.md
- docs/contracts/job-jsonl.md
```

## What the current project can do

The project can run this local flow:

```text
fixture or live collector input
  -> normalized job records/JSONL
  -> SQLite jobs/job_skills database
  -> basic JSON analytics queries
  -> FastAPI or CLI responses
```

Local fixture E2E example:

```bash
uv run --extra dev upwork-app-collect \
  --fixture tests/fixtures/visitor_job_search_response.json \
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
make dev APP_DB=/tmp/upwork-e2e.sqlite
```

Then call:

```text
GET  /health
POST /collect              # summary only
POST /collect/jobs         # preview/full normalized jobs
POST /ingest (prefer `jobs: [...]`; JSONL remains supported for pipeline compatibility)
POST /collect-and-ingest (MVP convenience endpoint returning new jobs and counts)
POST /runs/collect (run-style collect+ingest endpoint returning new jobs and counts)
GET  /analytics/summary
```

## Verification commands

```bash
make quality
make smoke
make e2e-smoke
```

Duplicate check:

```bash
npx jscpd --reporters ai --gitignore --min-lines 10 \
  --ignore "**/.venv/**,**/.mypy_cache/**,**/.pytest_cache/**,**/.ruff_cache/**,**/__pycache__/**,**/*.egg-info/**,**/uv.lock,.omx/**" .
```

Live smoke is explicit opt-in only:

```bash
make live-smoke QUERY="python"
```

Live evidence must be reported separately from fixture/local contract evidence.

## Common wrong assumptions to correct

- “The project auto-applies to jobs.” Wrong. Auto-apply/message generation is out of scope.
- “The project ranks jobs.” Wrong. Ranking is not implemented.
- “The project stores every collection run or observation.” Wrong. It stores only unique jobs and skills.
- “Analytics can infer client spend/country from text.” Wrong. Missing client fields become unknown/null.
- “Fixture tests prove live Upwork works.” Wrong. Fixture/local tests prove contracts only; live smoke is separate opt-in evidence.
- “New code should go under `packages/*`.” Wrong. New backend code should go under `src/upwork_app`.

## Minimal context bundle to attach

1. `README.md`
2. `docs/LLM_CONTEXT.md`
3. `docs/fastapi-backend-structure.md`
4. `docs/EXTERNAL_LLM_GUIDE.md`
5. `docs/contracts/job-jsonl.md`
6. Relevant source/tests under `src/upwork_app` and `tests`.

Do not paste `.omx/logs`, `.omx/state`, or runtime traces unless the question is specifically about OMX execution.
