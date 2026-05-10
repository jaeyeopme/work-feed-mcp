# upwork

Upwork job discovery pipeline monorepo입니다.

이 저장소의 목표는 Upwork job 데이터를 안정적으로 수집하고, 이후 agent/LLM이 분석에 활용할 수 있도록 구조화된 로컬 데이터 파이프라인을 제공하는 것입니다. 목적은 자동 지원/메시지 작성이 아니라 **분석 가능한 데이터 수집**입니다.

## LLM/agent quick context

처음 이 repo를 읽는 LLM/agent는 [`docs/LLM_CONTEXT.md`](docs/LLM_CONTEXT.md)를 먼저 확인하세요. 외부 LLM에게 프로젝트를 설명하거나 작업을 맡길 때는 [`docs/EXTERNAL_LLM_GUIDE.md`](docs/EXTERNAL_LLM_GUIDE.md)를 함께 제공하세요.

## 현재 MVP 상태

현재 구현된 MVP 경로는 다음과 같습니다.

```text
packages/collector  Upwork/fixture → normalized job JSONL stdout
packages/ingest     collector JSONL → SQLite
packages/analytics  SQLite → 기본 집계/조회 JSON
```

`packages/ranker`, `packages/report`는 향후 확장 경계만 잡혀 있으며 MVP 기능은 아닙니다.

## 모듈 경계

```text
packages/
  collector/   Upwork 수집과 normalized JSONL stdout만 담당
  ingest/      JSONL 검증, SQLite 저장, run/job/skill/raw record provenance 담당
  analytics/   SQLite를 읽어 summary/skills/jobs/budgets/runs/clients query 제공
  ranker/      향후 Jaeyeop-specific application value scoring 담당
  report/      향후 Discord/Markdown/HTML rendering 담당
```

### collector

- stdout에는 job JSONL record만 출력합니다.
- stderr에는 진단 메시지만 출력하며 credential/session/proxy/token을 redaction합니다.
- SQLite, snapshot, analytics, ranking, report, scheduler, notification, UI를 담당하지 않습니다.

### ingest

- collector JSONL을 file 또는 stdin으로 읽습니다.
- collector contract를 검증합니다.
- SQLite schema를 만들고 `ingest_runs`, `jobs`, `job_skills`, `job_observations`, `raw_records`를 저장합니다.
- `raw_records.payload_json`에는 upstream GraphQL/private payload가 아니라 collector가 출력한 normalized JSON object만 저장합니다.

### analytics

- SQLite만 읽습니다.
- JSONL을 직접 파싱하거나 collector를 호출하지 않습니다.
- client 관련 집계는 DB에 해당 column이 있을 때만 사용합니다.
- 없는 client field는 추론하지 않고 `unknown`/`null`로 처리합니다.

## CLI 예시

```bash
PYTHONPATH=packages/collector/src python -m upwork_collector collect \
  --fixture packages/collector/tests/fixtures/visitor_job_search_response.json \
  | PYTHONPATH=packages/ingest/src python -m upwork_ingest ingest \
      --db /tmp/upwork.sqlite \
      --input - \
      --query python

PYTHONPATH=packages/analytics/src python -m upwork_analytics query summary --db /tmp/upwork.sqlite
PYTHONPATH=packages/analytics/src python -m upwork_analytics query skills --db /tmp/upwork.sqlite
PYTHONPATH=packages/analytics/src python -m upwork_analytics query clients --db /tmp/upwork.sqlite
```

## 검증

Collector 변경 후:

```bash
make quality
make smoke
```

Ingest 변경 후:

```bash
cd packages/ingest
ruff format --check .
ruff check .
mypy src
pytest -q
make smoke
```

Analytics 변경 후:

```bash
cd packages/analytics
ruff format --check .
ruff check .
mypy src
pytest -q
```

Live smoke는 명시적으로 opt-in할 때만 실행합니다.

```bash
make live-smoke QUERY="python"
```
