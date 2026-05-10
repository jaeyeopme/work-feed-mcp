# PRD: upwork-collector Python scraper core

## 1. 문서 상태

- 상태: 승인됨, 구현 전 기준 문서
- 구현 대상: `/Users/jaeyeop/Workspace/upwork/packages/collector`
- 제품명/CLI명: `upwork-collector`
- Python package명: `upwork_collector`
- 원본 계획 provenance:
  - `.omx/context/upwork-collector-python-core-20260510T060609Z.md`
  - `.omx/plans/prd-upwork-collector-python-core-20260510T061043Z.md`
  - `.omx/plans/test-spec-upwork-collector-python-core-20260510T061043Z.md`

## 2. 제품 목표

Upwork job search 결과를 수집하고, downstream agent/system이 안정적으로 처리할 수 있도록 **한 줄에 하나의 normalized job JSON object**를 stdout으로 출력하는 Python-only collector core를 만든다.

이 MVP는 scraper core다. UI, watcher, scheduler, storage, recommendation, Go collector, Swift app이 아니다.

## 3. 핵심 원칙

1. **Collector 경계 유지**: Python은 scraping transport, GraphQL 처리, normalization, error mapping, CLI JSONL output만 소유한다.
2. **TDD 우선**: fixture/contract/failure-mode test를 먼저 작성하고, 테스트로 동작을 고정한다.
3. **Secret-safe by construction**: credential/session/proxy material은 commit, fixture, docs, stdout, stderr, logs, payload에 노출하지 않는다.
4. **Machine contract 우선**: stdout은 JSONL only, stderr는 diagnostics only, exit code는 stable하고 테스트된다.
5. **Fixture는 evidence가 아니라 contract test**: fixture는 local schema/CLI/normalization 계약을 고정하는 테스트 입력일 뿐이며, live 동작의 증거로 취급하지 않는다.
6. **Mock 성공 금지**: mock/fake transport로 Upwork 수집 성공을 주장하지 않는다. 실제 수집 성공은 live E2E/smoke에서만 인정한다.

## 4. 범위

### 4.1 In scope

예상 구조:

```text
/Users/jaeyeop/Workspace/upwork/packages/collector/
  pyproject.toml
  README.md
  AGENTS.md
  docs/
    PRD.md
    TEST_PLAN.md
    adr/0001-python-jsonl-collector.md
  src/upwork_collector/
    __init__.py
    cli.py
    transport.py
    graphql.py
    normalize.py
    credentials.py
    errors.py
    models.py
  tests/
    fixtures/
      visitor_job_search_response.json
      malformed_response.json
    test_normalize.py
    test_credentials.py
    test_cli_fixture.py
    test_error_exit_codes.py
    test_transport_contract.py
    test_live_smoke.py
```

기능 범위:

- CLI entrypoint `upwork-collector`
- fixture mode: sanitized fixture를 읽어 JSONL 출력, 네트워크 없음
- live mode/live smoke: 명시적 opt-in
- browser-like transport abstraction은 `transport.py`에 격리
- GraphQL endpoint/query/variables/response extraction은 `graphql.py`에 격리
- Upwork raw job result를 stable `Job` DTO로 normalize
- local credential/session reference loading
- credential/session/proxy-like value redaction
- typed error와 numeric exit code mapping
- README와 docs에 setup, CLI, fixture의 역할(local contract test), live smoke 조건, secret boundary 문서화

### 4.2 Out of scope

명시적 승인 전까지 하지 않는다.

- Swift
- UI
- watcher app behavior
- upfeed scheduler/API/storage 변경
- Go-native Upwork collector
- SQLite
- JSON snapshot writer
- default durable local state
- daemon/scheduler ownership
- recommendation, fit scoring, notification policy
- proxy acquisition docs
- reusable access-control/circumvention playbook

## 5. CLI 계약

### 5.1 Commands

Fixture mode:

```bash
upwork-collector collect --fixture tests/fixtures/visitor_job_search_response.json
```

Live collect, explicit env-gated opt-in:

```bash
UPWORK_COLLECTOR_LIVE=1 upwork-collector collect --query "python" --max-pages 1 --page-size 50 --live
```

Live smoke:

```bash
UPWORK_COLLECTOR_LIVE=1 upwork-collector live-smoke --query "python" --max-pages 1 --page-size 50
```

`python -m upwork_collector ...` equivalent도 문서화되어 있으면 허용한다.

### 5.2 Options

`collect`:

- `--fixture <path>`: sanitized fixture response를 읽는다. credentials/network 불필요.
- `--live`: 실제 Upwork transport를 활성화한다. 기본값은 off.
- `--query <text>`: Upwork search query.
- `--max-pages <int>`: MVP 기본값 `1`.
- `--page-size <int>`: MVP 기본값 `50`, 구현에서 안전하게 bound한다.
- 기본 live 수집량은 `max_pages=1` × `page_size=50` = 최대 50개 record이다. CLI 안전 bound는 최대 5 pages × 50 = 250개이다.
- `--output jsonl`: MVP의 유일한 output format.

`live-smoke`:

- command 자체가 live opt-in이다.
- `UPWORK_COLLECTOR_LIVE=1`도 함께 필요하다.
- visitor-token bootstrap은 내부 transport mode로 허용한다.
- credential/session-backed transport는 필요한 경우 local reference로만 읽는다.
- 필요한 credential/session prerequisite이 없으면 안전하게 실패/skip한다.

## 6. Stream 계약

- stdout: normalized job JSON object만, 한 줄에 하나
- stderr: diagnostics/warnings/errors only
- stderr에 job JSON record를 출력하지 않는다.
- stdout에 diagnostics를 출력하지 않는다.
- 어느 stream에도 credential/session/proxy raw value를 출력하지 않는다.

## 7. JSONL Job schema

필수 필드:

```json
{
  "source": "upwork",
  "id": "string",
  "title": "string",
  "description": "string",
  "url": "string",
  "skills": ["string"]
}
```

선택/nullable 필드:

```json
{
  "posted_at": "ISO-8601 string or null",
  "job_type": "string or null",
  "contractor_tier": "string or null",
  "hourly_min": "number or null",
  "hourly_max": "number or null",
  "fixed_amount": "number or null",
  "raw_id": "string or null"
}
```

URL은 가능한 경우 legacy response의 `cipherText`/`ciphertext`를 우선 사용한다. 현재 visitor live response처럼 numeric `id`만 있는 경우 Upwork permalink 형태 `~02{id}`로 정규화한다. 신뢰 가능한 permalink를 만들 수 없으면 모호한 record를 emit하지 말고 fail closed한다.

## 8. Exit code taxonomy

| Code | 이름                                 | 의미                                                                                              |
| ---: | ------------------------------------ | ------------------------------------------------------------------------------------------------- |
|    0 | success                              | 요청된 작업 성공. live success는 nonzero job record 필요.                                         |
|    2 | usage_error                          | invalid CLI arguments 또는 incompatible options                                                   |
|   10 | credential_required                  | live mode에 필요한 credential/session/token/cookie/local reference 누락 또는 invalid              |
|   20 | upstream_blocked                     | Upwork block/forbidden/access-denied 류 응답                                                      |
|   21 | rate_limited                         | Upwork rate limit/throttle 류 응답                                                                |
|   30 | upstream_schema_or_temporary_failure | GraphQL errors, malformed shape, missing required raw fields, timeout, retryable upstream failure |
|   40 | internal_failure                     | 예상하지 못한 local bug/invariant failure                                                         |

## 9. Credential/session boundary

허용:

- credential 없이 가능한 visitor-token bootstrap을 내부 live transport mode로 사용
- 필요한 경우 아래 local reference 읽기:
  - `UPWORK_COLLECTOR_SESSION_FILE`
  - `UPWORK_COLLECTOR_COOKIE_FILE`
  - `UPWORK_COLLECTOR_PROXY_URL`
  - `UPWORK_COLLECTOR_LIVE=1`
- `.gitignore`된 local file 읽기
- `missing`, `loaded`, `redacted`, `invalid` 같은 상태 metadata 보고

금지:

- real cookie, bearer token, proxy URL, session, private response commit
- raw credential/session/proxy material을 stdout/stderr/logs/exceptions에 출력
- reusable bypass instruction, proxy acquisition flow, access-control circumvention playbook 문서화
- credential/session 값을 API payload나 fixture에 포함

## 10. Module boundary

- `transport.py`: HTTP client setup, browser-like request behavior
- `graphql.py`: endpoint URL, query document, variables, response extraction
- `normalize.py`: raw job result node를 typed model로 변환
- `credentials.py`: local credential/session reference loading과 redaction
- `errors.py`: typed error와 exit code mapping
- `cli.py`: CLI orchestration; Upwork request internals나 persistence를 소유하지 않음

## 11. Acceptance criteria

1. 프로젝트 scaffold가 `/Users/jaeyeop/Workspace/upwork/packages/collector`에 존재한다.
2. `pyproject.toml`이 pytest/ruff/mypy 설정을 제공한다.
3. README/docs가 setup, CLI, TDD workflow, fixture의 역할(local contract test), live smoke 조건, secret boundary를 설명한다.
4. Fixture CLI mode가 valid JSONL을 stdout에 출력한다.
5. Diagnostics는 stderr에만 출력한다.
6. Normalization이 fixture GraphQL response를 stable schema로 변환한다.
7. Malformed fixture response는 typed error + exit code `30`으로 fail closed한다.
8. Missing live credential/session prerequisite은 exit code `10`으로 mapping된다.
9. Rate limit/block response는 각각 `21`/`20`으로 mapping된다.
10. Default tests는 network와 credentials 없이 실행된다.
11. 실제 Upwork 수집 성공은 live E2E/smoke에서만 인정하며, 명시적 활성화 + 실제 응답 + nonzero JSONL jobs 없이는 성공으로 보고하지 않는다.
12. SQLite, snapshot, scheduler, daemon state, Swift/UI/watcher, Go-native collector code를 기본 생성하지 않는다.
13. fixture/docs/tests/payload/stdout/stderr에 raw credential/session/proxy material이 없다.

## 12. 구현 완료 전 검증

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

Live smoke는 explicit opt-in과 prerequisite이 있을 때만 실행한다.
