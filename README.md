# upwork

Upwork job discovery backend입니다. 목적은 Upwork job 데이터를 안정적으로 수집하고, agent/LLM이 분석에 활용할 수 있도록 구조화된 로컬 데이터 파이프라인과 FastAPI HTTP 인터페이스를 제공하는 것입니다. 자동 지원/메시지 작성이 아니라 **분석 가능한 데이터 수집**이 범위입니다.

## 현재 구조

이 프로젝트는 일반적인 Python 백엔드 형태의 단일 root app으로 동작합니다.

```text
src/upwork_app/
  main.py                 FastAPI app entrypoint (`upwork_app.main:app`)
  api/routes/             HTTP endpoints
  schemas/                Pydantic request/response models
  services/               application orchestration
  repositories/           SQLite query/persistence helpers
  db/                     SQLite connection/schema
  domain/                 collector record validation/domain types
  integrations/upwork/    Upwork transport + normalization boundary
  cli/                    local batch CLIs
tests/                    API/service fixtures and tests
```

신규 작업의 source of truth는 `src/upwork_app`입니다. 별도 `packages/*` compatibility layer는 유지하지 않습니다.

## 책임 경계

```text
integrations/upwork  Upwork/fixture → normalized job records
services/ingestion   normalized JSONL → SQLite
services/analytics   SQLite → query result JSON
api/routes           HTTP request/response binding only
```

중요한 경계:

- Upwork integration은 normalized job record만 생산합니다.
- credential/session/proxy/token은 diagnostics에서 redaction되어야 합니다.
- SQLite persistence는 ingestion/db/repository 계층 책임입니다.
- analytics는 SQLite read-only입니다.
- ranking, auto-apply, message generation, notification, report delivery는 MVP 범위 밖입니다.
- HTTP API는 caller-selected DB path를 받지 않습니다. 서버 설정 `UPWORK_APP_DB` 또는 `make APP_DB=...`를 사용합니다.

## FastAPI 실행

```bash
make dev
```

실행 설정은 `make` 변수로 바꿀 수 있습니다.

```bash
make dev APP_DB=/tmp/upwork.sqlite APP_PORT=8080
make run APP_DB=/tmp/upwork.sqlite
```

주요 endpoint:

```text
GET  /health
POST /collect
POST /ingest               # accepts jobs[] for HTTP clients or jsonl for pipeline compatibility
POST /collect-and-ingest   # convenience MVP endpoint; run resources can replace this later
GET  /analytics/summary
GET  /analytics/skills
GET  /analytics/jobs
GET  /analytics/budgets
GET  /analytics/runs
GET  /analytics/clients
```

Fixture collect 예시:

```bash
curl -X POST http://127.0.0.1:8000/collect \
  -H 'content-type: application/json' \
  -d '{"fixture":"tests/fixtures/visitor_job_search_response.json"}'
```


HTTP ingest는 일반 클라이언트용으로 `jobs: [...]` 입력을 권장하고, 기존 JSONL 파이프라인 호환을 위해 `jsonl: "..."`도 지원합니다. 둘 중 하나만 보낼 수 있습니다.

## CLI 예시

```bash
uv run --extra dev upwork-app-collect \
  --fixture tests/fixtures/visitor_job_search_response.json \
  > /tmp/upwork-jobs.jsonl

uv run --extra dev upwork-app-ingest \
  --db /tmp/upwork.sqlite \
  --input /tmp/upwork-jobs.jsonl \
  --query python

uv run --extra dev upwork-app-analytics summary --db /tmp/upwork.sqlite
uv run --extra dev upwork-app-analytics skills --db /tmp/upwork.sqlite
uv run --extra dev upwork-app-analytics clients --db /tmp/upwork.sqlite
```

## 검증

```bash
make quality
make smoke
make e2e-smoke
```

중복 확인:

```bash
npx jscpd --reporters ai --gitignore --min-lines 10 \
  --ignore "**/.venv/**,**/.mypy_cache/**,**/.pytest_cache/**,**/.ruff_cache/**,**/__pycache__/**,**/*.egg-info/**,**/uv.lock,.omx/**" .
```

Live smoke는 명시적으로 opt-in할 때만 실행합니다.

```bash
make live-smoke QUERY="python"
```

## LLM/agent quick context

처음 이 repo를 읽는 LLM/agent는 [`docs/LLM_CONTEXT.md`](docs/LLM_CONTEXT.md)를 먼저 확인하세요. 외부 LLM에게 프로젝트를 설명하거나 작업을 맡길 때는 [`docs/EXTERNAL_LLM_GUIDE.md`](docs/EXTERNAL_LLM_GUIDE.md)를 함께 제공하세요.
