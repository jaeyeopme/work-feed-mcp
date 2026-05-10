# 테스트 계획: upwork-collector Python scraper core

## 1. 문서 상태

- 상태: 승인됨, 구현 전 기준 문서
- 구현 대상: `/Users/jaeyeop/Workspace/upwork-collector`
- 목표: TDD로 collector core 계약을 고정한다. Fixture는 evidence가 아니라 local contract test 입력으로만 사용한다.

## 2. 기본 전략

기본 검증은 deterministic, local, network-free여야 한다. Fixture는 schema/normalization/CLI 계약을 고정하는 테스트 입력일 뿐이다.

Live smoke는 별도 opt-in이며 unit/contract test를 대체하지 않는다. 반대로 fixture 기반 테스트나 mock/fake transport는 live 성공 증거로 취급하지 않는다. 실제 Upwork 수집 성공은 live E2E/smoke에서만 인정한다.

필수 품질 명령:

```bash
ruff format --check .
ruff check .
mypy src
pytest
```

## 3. Test pyramid

1. pure function / typed model unit tests
2. CLI stream, JSONL schema, exit code contract tests
3. sanitized fixture contract tests
4. opt-in live E2E/smoke tests
5. secret-leak/static checks

## 4. Fixture 요구사항

Fixtures는 synthetic 또는 sanitized여야 하며 아래 값을 포함하면 안 된다.

- cookies
- bearer tokens
- session IDs
- proxy URLs
- account-specific private data
- real account request headers
- private raw samples

필수 fixtures:

- `tests/fixtures/visitor_job_search_response.json`: job result 2개 이상 포함한 대표 GraphQL response
- `tests/fixtures/malformed_response.json`: 예상 path가 누락된 response

선택 fixtures:

- optional budget/hourly fields 누락
- required identity field 누락
- GraphQL `errors`
- blocked response
- rate-limited response

## 5. Normalization tests

파일: `tests/test_normalize.py`

필수 cases:

1. `test_normalizes_representative_graphql_response`
   - sanitized fixture를 normalized jobs로 변환
   - 필수 필드 존재 확인: `source`, `id`, `title`, `description`, `url`, `skills`
   - optional 필드가 값 또는 `None`으로 존재하는지 확인

2. `test_missing_optional_fields_are_safe`
   - budget/hourly/contractor tier 누락은 `None` 또는 안전한 기본값
   - optional omission 때문에 예외가 나면 안 됨

3. `test_missing_required_identity_fails_closed`
   - raw result `id`와 `job.cipherText`/`ciphertext` 모두 없으면 typed schema/upstream error

4. `test_malformed_response_shape_fails_closed`
   - 예상 GraphQL path 누락은 exit code `30`에 해당하는 typed error

5. `test_graphql_errors_fail_closed`
   - GraphQL `errors`가 있으면 명시적 partial policy 승인 전에는 partial success JSONL을 emit하지 않음

## 6. Model tests

파일: `tests/test_models.py`

- `Job` serialization은 JSON-compatible dict만 emit
- `skills`는 항상 list
- numeric fields는 number 또는 `None`
- datetime-like fields는 JSONL 출력 시 string 또는 `None`

## 7. Credentials/redaction tests

파일: `tests/test_credentials.py`

1. `test_fixture_mode_does_not_require_credentials`
   - fixture mode는 live credential/session 값을 읽지 않음

2. `test_live_mode_missing_credentials_maps_to_credential_required`
   - selected transport mode가 credential/session을 요구하고 값이 없으면 typed credential error
   - CLI exit code `10`

3. `test_local_file_reference_can_be_loaded_without_printing_value`
   - temp cookie/session file을 읽되 repr/str/diagnostics에 raw value 없음

4. `test_redacts_cookie_bearer_proxy_and_env_values`
   - cookie, bearer token, credential 포함 proxy URL, session file content, env var value redaction

5. `test_exceptions_are_redacted`
   - HTTP/client failure wrapping 시 raw secret이 exception message에 남지 않음

## 8. CLI fixture contract tests

파일: `tests/test_cli_fixture.py`

1. `test_fixture_collect_emits_jsonl_stdout_only`
   - `upwork-collector collect --fixture ...`
   - exit code `0`
   - stdout 각 line이 JSON parse 가능
   - stderr에 job JSON record 없음

2. `test_diagnostics_do_not_pollute_stdout`
   - diagnostics가 있어도 stdout은 JSONL only

3. `test_stderr_never_contains_secret_like_fixture_values`
   - synthetic secret-like env value가 stderr에 노출되지 않음

4. `test_invalid_cli_options_exit_usage_error`
   - incompatible `--fixture` + `--live`, invalid page size는 exit code `2`

5. `test_fixture_mode_does_not_create_state_files`
   - fixture CLI 실행 후 SQLite DB, snapshot JSON, scheduler/daemon/hidden durable state 생성 없음

## 9. Exit-code tests

파일: `tests/test_error_exit_codes.py`

| Scenario | Expected code |
|---|---:|
| Success | 0 |
| Invalid arguments | 2 |
| Missing/invalid live credential/session/token/cookie | 10 |
| Upstream blocked/forbidden/access-denied | 20 |
| Upstream rate limited/throttled | 21 |
| GraphQL errors, malformed shape, timeout, retryable upstream failure | 30 |
| Unexpected local bug/invariant failure | 40 |

필수 cases:

- typed error → exit code function unit test
- CLI-level usage, credential, schema/temp failure, internal failure
- synthetic response/status classification으로 blocked/rate-limited error mapping 확인. 단, 이를 수집 성공으로 표현하지 않음

## 10. GraphQL/parser contract tests

파일: 필요 시 `tests/test_graphql.py`, `tests/test_parser_contract.py`

- 기본 local tests는 network를 호출하지 않음
- endpoint constant는 `https://www.upwork.com/api/graphql/v1`
- request variables에는 paging offset/count와 optional query 포함
- budget filters는 검증 전 임의로 invent하지 않음
- parser/extractor는 `data.search.universalSearchNuxt.visitorJobSearchV1.results`를 읽음
- GraphQL `errors`는 typed upstream/schema error
- `visitor_gql_token` 같은 token 문자열은 redaction 대상임
- mock/fake transport 응답으로 “Upwork 수집 성공”을 주장하는 테스트를 작성하지 않음

## 11. Live smoke tests

파일: `tests/test_live_smoke.py`

Live tests는 아래 gate 없이는 skip 또는 safe refusal이어야 한다.

- explicit `live-smoke` command 또는 live test invocation
- `UPWORK_COLLECTOR_LIVE=1`
- selected transport mode가 요구하는 local credential/session reference
- pytest marker를 쓴다면 explicit `pytest -m live`

Cases:

1. `test_live_smoke_requires_explicit_enablement`
   - env gate 없으면 skip 또는 safe refusal

2. `test_live_missing_credentials_is_credential_required_when_selected_mode_requires_them`
   - credential/session-backed mode에서 prerequisite 없으면 exit code `10`, redacted diagnostics
   - visitor-token bootstrap mode는 안전하면 credential 없이 진행 가능

3. `test_live_collects_nonzero_jobs_when_credentials_available`
   - prerequisites가 있을 때만 실행
   - real Upwork request 수행
   - exit code `0`과 nonzero JSONL jobs 요구
   - local contract test 결과와 별도로 live smoke 결과를 기록

## 12. Secret-leak verification

완료 전 guard:

```bash
find . -name '*.sqlite' -o -name 'snapshot-*.json'
grep -RInE 'visitor_gql_token|Bearer [A-Za-z0-9._-]+|https?://[^[:space:]]+:[^[:space:]]+@|WEBSHARE|session|cookie' . \
  --exclude-dir=.git --exclude-dir=.venv
```

이 grep은 보조 guard일 뿐이다. Redaction tests와 fixture review를 대체하지 않는다.

## 13. TDD 구현 순서

1. `errors.py` tests와 exit-code mapping tests
2. `models.py`/normalization tests + sanitized fixtures
3. CLI fixture stdout/stderr tests
4. credential redaction tests
5. GraphQL/parser/error-classification contract tests
6. 최소 구현
7. README/docs 업데이트
8. quality gate 실행
9. local contract smoke 실행: JSONL/CLI/parser 계약만 확인
10. live E2E/smoke는 explicit approval/gate/prerequisite이 있을 때만 실행하고, 이것만 실제 수집 성공으로 인정

## 14. 완료 기준

구현 완료 보고에는 최소 아래 기준의 fresh output/status가 포함되어야 한다. Fixture 결과는 live evidence가 아니라 local contract 통과 여부로만 표현한다.

- `ruff format --check .` passed
- `ruff check .` passed
- `mypy src` passed
- `pytest` passed without network
- local contract smoke passed: live success가 아니라 JSONL/CLI/parser 계약 통과로만 표현
- secret-leak/static checks reviewed
- SQLite/snapshot/scheduler/daemon state가 기본 생성되지 않음 확인
- live E2E/smoke status:
  - `not run: no explicit live approval`
  - `not run: selected transport required credentials/session material that was unavailable`
  - `failed: <redacted reason>`
  - `passed: real Upwork response, nonzero JSONL jobs, no secret leakage observed`
