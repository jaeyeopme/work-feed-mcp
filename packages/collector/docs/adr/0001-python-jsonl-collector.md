# ADR 0001: Python-only JSONL Upwork collector core

## 상태

Accepted.

## 맥락

이 저장소는 `/Users/jaeyeop/Workspace/upwork/packages/collector`에 위치한 Upwork collector의 canonical 구현 대상이다.

이전 계획에서는 깨끗한 Python scraper core를 승인했고, UI/watcher/scheduler/storage/Swift/Go-native collector/SQLite/snapshot/recommendation 기능은 MVP 범위에서 제외했다.

기존 reference scraper `/Users/jaeyeop/Workspace/upwork-scraper/scraper.py`는 다음 근거로만 사용한다.

- browser-like HTTP stack이 필요할 수 있음
- visitor-token bootstrap 흐름
- Upwork GraphQL endpoint
- response traversal shape

하지만 legacy scraper의 SQLite persistence, JSON snapshot writing, standalone durable state, random sleep orchestration, proxy-pool ownership은 MVP로 port하지 않는다.

## 결정

Python package `upwork_collector`와 CLI `upwork-collector`를 만든다.

Collector는 normalized Upwork job record를 stdout에 JSONL로 출력한다. Diagnostics는 stderr로만 출력한다. Fixture는 local contract test 입력으로만 사용한다. Mock/fake transport로 수집 성공을 주장하지 않는다. 실제 Upwork 수집 성공은 live E2E/smoke 결과로만 인정한다.

Live smoke는 명시적으로 활성화한 경우에만 실행하며, 실제 Upwork 요청에서 nonzero JSONL job records가 나왔을 때만 성공으로 보고한다.

## 결정 동인

- collector boundary를 작게 유지한다.
- downstream integration은 JSONL machine contract로 가능하게 한다.
- legacy scraper의 유용한 transport 지식만 보존하고 stateful behavior는 배제한다.
- pytest/ruff/mypy 기반 TDD 구현을 가능하게 한다.
- credential/session/proxy leakage를 구조적으로 방지한다.

## 대안

### 대안 A: legacy scraper를 직접 port/wrap

거절. Live behavior 재사용은 빠르지만 SQLite, snapshot, proxy/state coupling, random sleeps, standalone orchestration이 MVP에 섞일 위험이 크다.

### 대안 B: upfeed 내부에 구현

거절. scheduler/API/storage scope가 다시 섞이고, local contract test와 live smoke의 의미가 흐려진다.

### 대안 C: Go-native collector 또는 Swift/UI 앱

거절. 승인된 scope는 Python-only collector core이며 UI/watcher/Go-native collector는 non-goal이다.

## 결과

- 초기 구현은 tests, fixtures, CLI contract, typed errors, redaction, module boundary에 집중한다.
- fixture 기반 테스트나 mock/fake transport 통과는 live success가 아니다.
- live behavior는 별도 opt-in E2E/smoke로만 증명하고 별도 보고한다.
- `transport.py`가 browser-like HTTP details를 격리한다.
- 정상 local contract test/live collection은 기본 durable state를 만들지 않는다.

## 제약

- stdout: JSONL job records only
- stderr: redacted diagnostics only
- raw cookies, bearer tokens, session IDs, proxy URLs, private responses, account-specific samples는 commit/docs/fixtures/stdout/stderr/logs/payload에 금지
- proxy acquisition docs 또는 reusable bypass/circumvention playbooks 금지

## 검증 계획

```bash
ruff format --check .
ruff check .
mypy src
pytest
```

Local contract smoke:

```bash
upwork-collector collect --fixture tests/fixtures/visitor_job_search_response.json > /tmp/upwork-collector-fixture.jsonl
python -c 'import json,sys; [json.loads(line) for line in sys.stdin if line.strip()]' < /tmp/upwork-collector-fixture.jsonl
```

Live smoke는 `UPWORK_COLLECTOR_LIVE=1`로 명시적으로 실행했고 실제 Upwork response에서 nonzero JSONL jobs가 나왔을 때만 passed로 보고한다.
