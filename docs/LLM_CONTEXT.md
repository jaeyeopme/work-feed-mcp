# LLM Context: Upwork data pipeline

이 문서는 LLM/agent가 이 저장소를 처음 읽을 때 기준으로 삼는 빠른 컨텍스트입니다. 세부 구현은 각 package README와 source/test를 확인하세요.

## 현재 한 줄 요약

현재 구현된 MVP는 다음 경로입니다.

```text
Upwork/fixture data
  -> packages/collector: normalized job JSONL stdout
  -> packages/ingest: JSONL validation + SQLite persistence
  -> packages/analytics: SQLite-only basic queries
```

`packages/ranker`와 `packages/report`는 아직 구현되지 않았습니다.

## Product intent

목표는 **Upwork 지원 자동화**가 아니라 **안정적인 분석 가능 데이터 수집**입니다.

MVP가 보장해야 하는 것은 다음입니다.

- job 데이터를 normalized JSONL로 수집한다.
- JSONL을 SQLite에 저장한다.
- SQLite에서 기본 집계/조회가 가능하다.
- 나중에 agent/LLM/ranker가 활용할 수 있는 구조를 만든다.

MVP가 하지 않는 것은 다음입니다.

- LLM scoring/ranking
- auto-apply
- proposal/message generation
- Discord/Markdown/HTML report rendering
- scheduler/notification/UI
- proxy acquisition 또는 access-control bypass guidance

## Source of truth 우선순위

1. Root `AGENTS.md` — 전체 monorepo 경계와 금지사항
2. `README.md` — 현재 MVP 상태와 사용 흐름
3. `docs/contracts/job-jsonl.md` — collector JSONL contract
4. `packages/*/README.md` — package별 역할/CLI/검증
5. `packages/*/src`와 `packages/*/tests` — 실제 구현과 검증 근거
6. `.omx/*` — planning/runtime provenance; 현재 구현 판단의 1차 기준은 아님

## Implemented modules

### `packages/collector` — implemented

역할:

- Upwork/fixture 응답을 normalized job JSONL로 출력한다.
- stdout에는 job record만 출력한다.
- stderr에는 redacted diagnostics만 출력한다.

절대 하지 말아야 할 일:

- SQLite 저장
- durable local state
- analytics/ranking/reporting
- scheduling/notification/UI

주요 command:

```bash
PYTHONPATH=packages/collector/src python -m upwork_collector collect \
  --fixture packages/collector/tests/fixtures/visitor_job_search_response.json
```

### `packages/ingest` — implemented

역할:

- collector JSONL을 file 또는 stdin에서 읽는다.
- collector contract를 검증한다.
- SQLite DB를 만든다.
- run/job/skill/observation/raw-record provenance를 저장한다.

주요 tables:

- `ingest_runs`
- `jobs`
- `job_skills`
- `job_observations`
- `raw_records`

중요 규칙:

- `raw_records.payload_json`은 collector가 출력한 normalized JSON object만 저장한다.
- upstream GraphQL response, credential, session token, proxy, private payload는 저장하지 않는다.

주요 command:

```bash
PYTHONPATH=packages/ingest/src python -m upwork_ingest ingest \
  --db /tmp/upwork.sqlite \
  --input jobs.jsonl \
  --query python
```

stdin도 지원합니다.

```bash
cat jobs.jsonl | PYTHONPATH=packages/ingest/src python -m upwork_ingest ingest \
  --db /tmp/upwork.sqlite \
  --input - \
  --query python
```

### `packages/analytics` — implemented

역할:

- SQLite만 읽는다.
- 기본 집계/조회 결과를 JSON으로 출력한다.
- JSONL을 직접 파싱하지 않는다.
- collector를 호출하지 않는다.
- DB를 mutate하지 않는다.

지원 query:

- `summary`
- `skills`
- `jobs`
- `budgets`
- `runs`
- `clients`

주요 command:

```bash
PYTHONPATH=packages/analytics/src python -m upwork_analytics query summary --db /tmp/upwork.sqlite
PYTHONPATH=packages/analytics/src python -m upwork_analytics query skills --db /tmp/upwork.sqlite
PYTHONPATH=packages/analytics/src python -m upwork_analytics query clients --db /tmp/upwork.sqlite
```

Client analytics 규칙:

- SQLite `jobs` table에 client column이 있으면 해당 field만 집계한다.
- field가 없으면 `unknown`/`null` bucket으로 반환한다.
- title/description에서 client spend, country, verification 등을 추론하지 않는다.

## Not implemented modules

### `packages/ranker` — not implemented

의도된 미래 역할:

- SQLite/analytics 데이터를 읽어 Jaeyeop-specific application value score를 만든다.
- LLM scoring/ranking은 여기에 속한다.

현재 상태:

- placeholder only
- MVP 범위 아님

### `packages/report` — not implemented

의도된 미래 역할:

- ranked jobs 또는 analytics 결과를 Discord/Markdown/HTML로 rendering한다.

현재 상태:

- placeholder only
- MVP 범위 아님

## End-to-end local flow

Fixture 기반 local E2E:

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

Expected behavior:

- `summary`는 jobs/runs/observations/raw_records count를 반환한다.
- `skills`는 normalized skill frequency를 반환한다.
- `clients`는 현재 rich client field가 없으므로 `available: false`, `unknown`, `value: null` bucket을 반환한다.

## Verification commands

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

Live smoke는 명시적 opt-in일 때만 실행합니다.

```bash
make live-smoke QUERY="python"
```

Live 결과는 fixture/local contract evidence와 분리해서 보고해야 합니다.

## Common agent mistakes to avoid

- `collector`에 SQLite 저장을 추가하지 마세요.
- `analytics`가 collector를 직접 호출하게 만들지 마세요.
- client field가 없는데 title/description에서 client 정보를 추론하지 마세요.
- `ranker`/`report`가 구현된 것처럼 문서화하지 마세요.
- LLM ranking/auto-apply를 MVP 기능으로 넣지 마세요.
- `.omx` runtime artifact를 제품 소스 오브 트루스로 취급하지 마세요.
