# External LLM Guide: using the Upwork data engine

이 문서는 ChatGPT, Claude, Gemini 같은 외부 LLM에게 이 프로젝트를 설명하고 작업을 맡길 때 붙여넣기 좋은 가이드입니다.

목표는 외부 LLM이 이 저장소를 **지원 자동화 도구**나 웹 백엔드로 오해하지 않고, 현재 구현된 **수집 → SQLite 저장 → 기본 분석 → CLI 제공** 흐름을 올바르게 사용/확장하도록 만드는 것입니다.

## Copy-paste project brief

```text
You are helping with a CLI-first Upwork job discovery data engine.

Current structure:
- src/upwork_app/services: collect, ingest, and analytics use cases.
- src/upwork_app/repositories: SQLite query/persistence helpers.
- src/upwork_app/db: SQLite schema/connection helpers.
- src/upwork_app/domain: collector-record validation/domain types.
- src/upwork_app/integrations/upwork: Upwork transport, credentials, GraphQL, normalization.
- src/upwork_app/cli: local batch CLIs for agent/OpenClaw usage.
- tests: CLI/service tests and fixtures.

Product intent:
- Stable, deduplicated job storage for later external LLM/OpenClaw selection.
- OpenClaw acts as UI/orchestrator/recommendation layer.
- Not Upwork application automation.
- No auto-apply, proposal/message generation, backend ranking, app-native scheduler daemon, or report delivery in the core data engine. OS schedulers may call one-shot CLI commands.

Hard boundaries:
- Keep Upwork collection dumb and secret-safe.
- Store only deduplicated jobs and job skills, not upstream GraphQL/private payloads, run history, or observation logs.
- SQLite persistence belongs in ingestion/db/repository layers.
- Analytics reads SQLite only.
- Client analytics must not infer missing client fields from title/description. If client columns are absent, return unknown/null.
- Live collection requires explicit opt-in.

Use these docs as source of truth:
- README.md
- docs/LLM_CONTEXT.md
- docs/contracts/job-jsonl.md
```

## What the current project can do

The project can run this local flow:

```text
fixture or live collector input
  -> normalized job records/JSONL
  -> SQLite jobs/job_skills database
  -> basic JSON analytics queries
  -> CLI responses for OpenClaw/agent usage
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

One-shot live collect + ingest helper:

```bash
make collect-live-once QUERY="python" APP_DB=./data/upwork.sqlite
```

Scheduled multi-query one-shot CLI for OS schedulers:

```bash
UPWORK_COLLECTOR_LIVE=1 uv run upwork-app collect-scheduled \
  --db ./data/upwork.sqlite \
  --queries "python,scraping" \
  --max-pages 1 \
  --page-size 50
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

Default live smoke asks Upwork for 50 jobs in one visitor GraphQL page, matching the observed legacy scraper request shape. Success means normalized JSONL output from this data engine, not scraper-owned SQLite rows or raw snapshots. Live evidence must be reported separately from fixture/local contract evidence. Do not add proxy acquisition, access-control bypass, or raw snapshot persistence guidance to this repo.

## Common wrong assumptions to correct

- “The project auto-applies to jobs.” Wrong. Auto-apply/message generation is out of scope.
- “The project ranks jobs in backend code.” Wrong. Ranking belongs in OpenClaw skills unless explicitly promoted later.
- “The project stores every collection run or observation.” Wrong. It stores only unique jobs and skills.
- “Analytics can infer client spend/country from text.” Wrong. Missing client fields become unknown/null.
- “Fixture tests prove live Upwork works.” Wrong. Fixture/local tests prove contracts only; live smoke is separate opt-in evidence.
- “New code should go under `packages/*`.” Wrong. New data-engine code should go under `src/upwork_app`.

## Minimal context bundle to attach

1. `README.md`
2. `docs/LLM_CONTEXT.md`
3. `docs/EXTERNAL_LLM_GUIDE.md`
4. `docs/contracts/job-jsonl.md`
5. Relevant source/tests under `src/upwork_app` and `tests`.

Do not paste `.omx/logs`, `.omx/state`, or runtime traces unless the question is specifically about OMX execution.
