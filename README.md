# upwork

Upwork job discovery를 위한 **CLI-first 로컬 데이터 엔진**입니다.

역할은 단순합니다.

```text
Upwork/fixture 수집
  -> normalized JSONL
  -> SQLite에 중복 없이 적재
  -> CLI로 조회/분석
  -> OpenClaw가 UI/오케스트레이션/추천 담당
```

이 저장소는 웹 애플리케이션이 아닙니다. FastAPI 서버는 제거되었고, OpenClaw나 사람이 호출하기 좋은 CLI 명령을 제공하는 것이 핵심입니다.

자동 지원, proposal/message 생성, auto-apply는 범위 밖입니다.

## 설치 / 준비

필요한 것:

- Python 3.11+
- `uv`

처음 실행 전 의존성은 `uv run`이 자동으로 맞춥니다.

```bash
uv run --extra dev pytest -q
```

## 가장 빠른 로컬 사용법: fixture로 수집 → 적재 → 조회

실제 Upwork에 접속하지 않고 전체 로컬 흐름을 확인하는 방법입니다.

```bash
# 1. fixture 응답을 normalized JSONL로 변환
uv run --extra dev upwork-app-collect \
  --fixture tests/fixtures/visitor_job_search_response.json \
  > /tmp/upwork-jobs.jsonl

# 2. JSONL을 SQLite에 중복 없이 적재
uv run --extra dev upwork-app-ingest \
  --db /tmp/upwork.sqlite \
  --input /tmp/upwork-jobs.jsonl \
  --query python

# 3. 저장된 데이터 조회
uv run --extra dev upwork-app-analytics summary --db /tmp/upwork.sqlite
uv run --extra dev upwork-app-analytics skills --db /tmp/upwork.sqlite
uv run --extra dev upwork-app-analytics jobs --db /tmp/upwork.sqlite
uv run --extra dev upwork-app-analytics budgets --db /tmp/upwork.sqlite
uv run --extra dev upwork-app-analytics clients --db /tmp/upwork.sqlite
```

동일한 fixture를 다시 ingest하면 기존 `job_id`는 skip됩니다.

```bash
uv run --extra dev upwork-app-ingest \
  --db /tmp/upwork.sqlite \
  --input /tmp/upwork-jobs.jsonl \
  --query python
```

`upwork-app-ingest` 출력에는 OpenClaw가 바로 사용할 수 있는 `new_jobs`가 포함됩니다.

```json
{
  "seen_count": 2,
  "inserted_count": 0,
  "skipped_count": 2,
  "new_jobs": []
}
```

## 자주 쓰는 Make 명령

```bash
# 품질 검사: format check, lint, mypy, pytest
make quality

# fixture collect가 JSONL을 정상 출력하는지 확인
make smoke

# fixture collect -> ingest -> analytics 전체 확인
make e2e-smoke
```

## CLI 명령 reference

### `upwork-app-collect`

Upwork fixture 또는 live 응답을 normalized JSONL로 출력합니다.

```bash
uv run --extra dev upwork-app-collect --fixture <fixture-json>
uv run --extra dev upwork-app-collect --live --query "python" --max-pages 1 --page-size 50
```

옵션:

- `--fixture PATH`: fixture JSON 파일에서 수집
- `--live`: 실제 Upwork live 수집
- `--query TEXT`: 검색어
- `--max-pages N`: 최대 5
- `--page-size N`: 최대 50

주의:

- live 수집은 실제 Upwork에 접속합니다.
- live 수집은 명시적 opt-in 상황에서만 실행하세요.
- proxy/token은 로그에 노출되지 않아야 합니다.
- 이 저장소는 proxy 획득, access-control 우회, scraper snapshot 저장을 안내하지 않습니다.

### `upwork-app-ingest`

collector JSONL을 SQLite에 적재합니다. `job_id` 기준으로 중복을 건너뜁니다.

```bash
uv run --extra dev upwork-app-ingest \
  --db ./data/upwork.sqlite \
  --input /tmp/upwork-jobs.jsonl \
  --query "python"
```

옵션:

- `--db PATH`: SQLite DB 경로
- `--input PATH`: collector JSONL 경로. `-`는 stdin
- `--query TEXT`: 이 입력을 만들 때 사용한 검색어 메타데이터

출력은 JSON입니다.

주요 필드:

- `seen_count`: 입력에서 본 record 수
- `inserted_count`: 새로 inserted 된 job 수
- `skipped_count`: 이미 있어서 skip 된 job 수
- `new_jobs`: 이번 ingest에서 새로 들어온 job 목록
- `db_path`: DB 경로
- `source_query`: 검색어

OpenClaw 추천은 우선 `new_jobs`만 대상으로 돌리면 됩니다.

### `upwork-app collect-scheduled` / `upwork-app-collect-scheduled`

OS scheduler가 호출하기 위한 one-shot live 수집+적재 명령입니다. 기본 서버 경로는 검색어 없이 최신 공고를 최대 250개(`--max-pages 5 --page-size 50`) 훑습니다. systemd/cron/launchd가 반복 실행을 담당하고, 앱 자체 daemon은 없습니다.

```bash
UPWORK_COLLECTOR_LIVE=1 uv run upwork-app collect-scheduled \
  --db ./data/upwork.sqlite \
  --max-pages 5 \
  --page-size 50
```

특정 검색어만 보고 싶을 때만 수동/고급 옵션으로 `--queries`를 붙입니다.

```bash
UPWORK_COLLECTOR_LIVE=1 uv run upwork-app collect-scheduled \
  --db ./data/upwork.sqlite \
  --queries "python,scraping" \
  --max-pages 5 \
  --page-size 50
```

옵션:

- `--db PATH`: SQLite DB 경로
- `--queries TEXT`: optional comma-separated 검색어 목록. 생략하면 unfiltered/latest 수집
- `--max-pages N`: 최대 5
- `--page-size N`: 최대 50

출력 JSON에는 `run_id`, query별 `seen_count`, `inserted_count`, `skipped_count`, `attempts`가 포함됩니다. 기본 unfiltered 수집의 `query`는 JSON `null`입니다. 이 명령은 추천/랭킹을 하지 않습니다. 추천 후보 선정과 이유 작성은 agent skill 레이어 책임입니다.

### `upwork-app scheduler-status`

SQLite에 저장된 scheduled collection run history를 agent-readable JSON으로 조회합니다. systemd journal을 직접 파싱하지 않아도 최근 수집 상태를 확인할 수 있습니다.

```bash
uv run --extra dev upwork-app scheduler-status --db ./data/upwork.sqlite --limit 5
```

주요 필드:

- `last_run`: 최근 run의 `status`, 시작/종료 시각, duration, 총 seen/inserted/skipped, redacted error
- `recent_runs`: 최근 run 목록
- `recent_results`: 최근 run의 query별 결과. 기본 unfiltered 수집은 `query: null`

### `upwork-app-analytics`

SQLite DB를 조회합니다.

```bash
uv run --extra dev upwork-app-analytics summary --db ./data/upwork.sqlite
uv run --extra dev upwork-app-analytics skills --db ./data/upwork.sqlite
uv run --extra dev upwork-app-analytics jobs --db ./data/upwork.sqlite
uv run --extra dev upwork-app-analytics jobs --db ./data/upwork.sqlite --skill Python
uv run --extra dev upwork-app-analytics jobs --db ./data/upwork.sqlite --title backend
uv run --extra dev upwork-app-analytics budgets --db ./data/upwork.sqlite
uv run --extra dev upwork-app-analytics clients --db ./data/upwork.sqlite
```

쿼리 종류:

- `summary`: job/skill 개수 요약
- `skills`: skill별 빈도
- `jobs`: 저장된 job 목록. `--skill`, `--title` 필터 가능
- `budgets`: budget/hourly 관련 요약
- `clients`: client 관련 요약. 현재 schema에 없는 client 필드는 `unknown`으로 반환

## Live 수집 사용법

### 1회 live 수집만 테스트

```bash
make live-smoke QUERY="python" MAX_PAGES=1 PAGE_SIZE=50
```

이 명령은 live collect만 실행하고 DB에 저장하지 않습니다. 성공 기준은 scraper 전용 SQLite나 raw snapshot이 아니라 normalized JSONL record 출력입니다. `PAGE_SIZE=50`은 Upwork 요청의 `paging.count=50`으로 전달됩니다.

### live 수집 후 바로 SQLite에 적재

```bash
make collect-live-once \
  QUERY="python" \
  APP_DB="$(pwd)/data/upwork.sqlite" \
  MAX_PAGES=1 \
  PAGE_SIZE=50
```

내부 흐름:

```text
upwork-app-collect --live
  -> temp JSONL
  -> upwork-app-ingest --db APP_DB
  -> ingest 결과 JSON 출력
```

`collect-live-once`는 OpenClaw나 OS scheduler가 호출하기 좋은 현재의 one-shot primitive입니다.

### scheduler용 live 수집 후 SQLite 적재

서버 scheduler는 `collect-scheduled`를 호출하는 방식이 권장됩니다. 기본값은 검색어 없이 최신 공고 최대 250개를 수집합니다. 이 명령은 앱 내부 scheduler가 아니라 **one-shot CLI**입니다. 반복 실행은 systemd/cron/launchd 같은 OS scheduler가 담당합니다.

```bash
UPWORK_COLLECTOR_LIVE=1 uv run upwork-app collect-scheduled \
  --db ./data/upwork.sqlite \
  --max-pages 5 \
  --page-size 50
```

특정 공고군만 보고 싶을 때는 optional `--queries`를 사용합니다. comma로 나누고, 앞뒤 공백을 제거하고, 빈 항목은 버립니다.

```bash
UPWORK_COLLECTOR_LIVE=1 uv run upwork-app collect-scheduled \
  --db ./data/upwork.sqlite \
  --queries "python,scraping,automation" \
  --max-pages 5 \
  --page-size 50
```

성공 시 `run_id`와 query별 count-only JSON summary를 출력합니다. 중간 query가 실패하면 non-zero exit 하며, 이미 완료된 query ingest와 run history는 유지됩니다.

최근 scheduler 상태 조회:

```bash
uv run --extra dev upwork-app scheduler-status --db ./data/upwork.sqlite --limit 5
```

## 서버 설치 / 주기 실행

앱 내부 daemon scheduler는 없습니다. 주기 실행은 OS scheduler가 one-shot CLI를 호출하는 방식입니다. Linux 서버에서는 `systemd --user` timer를 권장합니다.

현재 서버 설치 계획의 기본 경로:

```text
repo: /home/ubuntu/upwork
runtime: /home/ubuntu/upwork-data
secret env: /home/ubuntu/upwork-data/config/upwork.env
systemd units: ~/.config/systemd/user/upwork-collector.{service,timer}
```

상세 설치 절차와 systemd unit 예시는 `docs/server-install.md`와 `deploy/systemd/`를 참고하세요.

기본 주기 권장값은 60분, 검색어 없는 latest scan, `--max-pages 5`, `--page-size 50`입니다. 연속 실행은 block을 유발할 수 있으므로 query/page를 늘리기 전에 journal을 확인하세요.

## OpenClaw에서 쓰는 방식

OpenClaw는 이 repo를 직접 구현체로 확장하기보다, CLI를 호출하는 UI/orchestrator로 사용하는 것이 목표입니다.

권장 cycle:

```text
1. OS scheduler가 `collect-scheduled`를 주기 실행
2. agent skill이 SQLite jobs/job_skills와 `scheduler-status` JSON을 조회
3. 새 공고나 필터링된 공고를 추천 후보로 출력
4. 추천/선호 memory는 OpenClaw skill 내부 파일에 저장
5. 수집 자체의 반복 실행은 systemd/cron/launchd가 담당
```

권장 skill 순서:

```text
CLI/systemd timer                # 서버의 주기 수집 설정/실행
upwork-app scheduler-status      # 최근 scheduled run 상태 JSON 조회
skills/upwork-data-engine        # DB 조회/필터링/추천 후보 출력
```

## 현재 구조

```text
src/upwork_app/
  services/               collection/ingestion/analytics use cases
  repositories/           SQLite query/persistence helpers
  db/                     SQLite connection/schema
  domain/                 collector record validation/domain types
  integrations/upwork/    Upwork transport + normalization boundary
  cli/                    local batch CLIs for OpenClaw/agent usage
tests/                    CLI/service fixtures and tests
scripts/                  local operational helpers
```

## 책임 경계

```text
integrations/upwork  Upwork/fixture → normalized job records
services/collector   collection use case
services/ingestion   normalized JSONL → SQLite
services/analytics   SQLite → query result JSON
cli                  stable command surface for OpenClaw and local batch usage
```

중요한 경계:

- Upwork integration은 normalized job record만 생산합니다.
- proxy/token은 diagnostics에서 redaction되어야 합니다.
- SQLite persistence는 ingestion/db/repository 계층 책임입니다.
- SQLite에는 중복 없는 `jobs`/`job_skills`와 scheduled collection 운영 요약(`collector_runs`, `collector_run_results`)만 저장합니다. raw payload archive나 per-job observation log는 저장하지 않습니다.
- analytics는 SQLite read-only입니다.
- ranking, auto-apply, message generation, notification, report delivery는 이 데이터 엔진 범위 밖입니다. 추천/랭킹은 OpenClaw skill 레이어에서 다룹니다.
- scheduler는 앱 내부 daemon이 아닙니다. CLI가 one-shot 수집 명령과 systemd/OS scheduler 설정 표면을 제공하고, 실제 반복 실행은 OS scheduler가 담당합니다.


## CI/CD

- CI: `.github/workflows/quality.yml` runs `make quality`, `make smoke`, and `make e2e-smoke` on push/pull request. It does not run live collection.
- CD: `.github/workflows/deploy-server.yml` is manual (`workflow_dispatch`) and deploys to the personal Linux server over SSH using repository secrets. It fast-forwards the server checkout, syncs the systemd user units, restarts the timer, and prints `scheduler-status` when the DB exists.

Required CD secrets:

```text
UPWORK_SERVER_HOST
UPWORK_SERVER_USER
UPWORK_SERVER_SSH_KEY
```

Live collection remains timer-owned; the deploy workflow does not run `make live-smoke`.

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
make collect-live-once QUERY="python" APP_DB=./data/upwork.sqlite
```

Live 결과는 Upwork/network 상태에 따라 달라질 수 있으므로 fixture/local contract 검증과 분리해서 보고하세요. 기본 품질 게이트는 `make quality`, `make smoke`, `make e2e-smoke`입니다.

## LLM/agent quick context

처음 이 repo를 읽는 LLM/agent는 [`docs/LLM_CONTEXT.md`](docs/LLM_CONTEXT.md)를 먼저 확인하세요. 외부 LLM에게 프로젝트를 설명하거나 작업을 맡길 때는 [`docs/EXTERNAL_LLM_GUIDE.md`](docs/EXTERNAL_LLM_GUIDE.md)를 함께 제공하세요.
