# upwork-collector

`upwork-collector`는 Upwork 검색 결과를 수집해 **정규화된 JSONL(job record per line)** 로 출력하는 Python 전용 scraper core입니다.

이 모듈은 collector core만 다룹니다. UI, watcher, scheduler, storage engine, Go collector, Swift 앱, upfeed 통합은 현재 범위가 아닙니다.

## 현재 상태

- 구현 대상 경로: `/Users/jaeyeop/Workspace/upwork/packages/collector`
- 현재 단계: MVP 구현 진행됨. Local contract tests는 통과해야 하며, 실제 수집 성공은 live E2E/smoke로만 인정합니다.
- 승인된 원본 계획 산출물은 `.omx/` 아래에 보관되어 있습니다.
- 사람이 읽는 repo-local 기준 문서는 `docs/` 아래를 canonical 문서로 사용합니다.

## 핵심 문서

- [PRD](docs/PRD.md) — 무엇을 만들고 어디까지 만들지
- [테스트 계획](docs/TEST_PLAN.md) — TDD 순서, 품질 게이트, 완료 기준
- [ADR 0001: Python JSONL collector 결정](docs/adr/0001-python-jsonl-collector.md) — 왜 이 구조를 선택했는지

원본 워크플로 provenance:

- `.omx/context/upwork-collector-python-core-20260510T060609Z.md`
- `.omx/plans/prd-upwork-collector-python-core-20260510T061043Z.md`
- `.omx/plans/test-spec-upwork-collector-python-core-20260510T061043Z.md`

## 목표

Upwork job search 응답을 수집하고, downstream agent/system이 처리하기 쉬운 안정적인 JSONL schema로 출력합니다.

기본 성공 기준:

1. fixture mode는 네트워크 없이 동작합니다.
2. stdout에는 job JSONL record만 출력합니다.
3. stderr에는 진단 메시지만 출력하며 secret은 redaction합니다.
4. live smoke는 명시적으로 켠 경우에만 실행합니다.
5. fixture는 local contract test로만 사용하고, live 성공 증거로 취급하지 않습니다.

## 설치와 실행

개발 환경에서는 editable install로 CLI entrypoint를 등록합니다.

```bash
python -m pip install -e ".[dev]"
```

기본 로컬 실행은 `make smoke`를 사용합니다. 이 명령은 sanitized fixture를 입력으로 CLI를 실행하고, 출력된 JSONL이 파싱 가능한 JSON인지 확인합니다.

```bash
make smoke
```

다른 fixture나 출력 경로를 쓰려면 make 변수로 넘깁니다.

```bash
make smoke FIXTURE=tests/fixtures/missing_optional_fields_response.json SMOKE_OUT=/tmp/upwork-collector-smoke.jsonl
```

전체 로컬 품질 게이트는 `make quality`입니다.

```bash
make quality
```

Live smoke는 실제 Upwork 요청을 수행하므로 명시적으로 opt-in해야 합니다. 기본 query는 `python`입니다.

기본 live 수집량은 `MAX_PAGES=1`, `PAGE_SIZE=50`이므로 한 번 실행하면 최대 50개 job record를 출력합니다. CLI bound는 `--max-pages <= 5`, `--page-size <= 50`이므로 명시적으로 올릴 수 있는 최대 요청량은 250개입니다.

```bash
make live-smoke
make live-smoke QUERY="python" MAX_PAGES=1 PAGE_SIZE=50
```

개별 CLI를 직접 실행할 수도 있습니다.

```bash
upwork-collector collect --fixture tests/fixtures/visitor_job_search_response.json
python -m upwork_collector collect --fixture tests/fixtures/visitor_job_search_response.json
UPWORK_COLLECTOR_LIVE=1 upwork-collector live-smoke --query "python" --max-pages 1 --page-size 50
```

현재 CLI help:

```bash
upwork-collector --help
upwork-collector collect --help
upwork-collector live-smoke --help
```


## 테스트 정책

이 프로젝트는 mock/fake transport로 Upwork 수집 성공을 주장하지 않습니다.

Local tests는 아래처럼 외부 네트워크가 필요 없는 순수 계약만 검증합니다.

- JSONL serialization
- CLI argument validation
- exit code mapping
- redaction
- parser/normalizer의 구조적 동작

실제 Upwork 수집 성공은 live E2E/smoke로만 인정합니다. Live 테스트는 명시적으로 활성화해야 하며, 실제 Upwork 응답에서 nonzero job records가 나와야 성공입니다.

## CLI 계약

Fixture mode, network-free:

```bash
upwork-collector collect --fixture tests/fixtures/visitor_job_search_response.json
```

Live smoke, explicit opt-in:

```bash
UPWORK_COLLECTOR_LIVE=1 upwork-collector live-smoke --query "python"
UPWORK_COLLECTOR_LIVE=1 upwork-collector live-smoke --query "python" --max-pages 1 --page-size 50
```

`live-smoke`와 `collect --live`는 visitor-token bootstrap을 먼저 시도합니다. 일반적인 visitor 수집은 별도 cookie/session 없이 동작할 수 있습니다. 필요한 경우에만 `.gitignore`된 local reference로 `UPWORK_COLLECTOR_COOKIE_FILE`, `UPWORK_COLLECTOR_SESSION_FILE`, `UPWORK_COLLECTOR_PROXY_URL`을 읽습니다.

`python -m upwork_collector ...` 형태도 문서화된 경우 허용합니다.

## 출력 계약

stdout은 JSONL only입니다. 한 줄에 하나의 normalized job JSON object를 출력합니다.

필수 필드:

- `source`
- `id`
- `title`
- `description`
- `url`
- `skills`

선택/nullable 필드:

- `posted_at`
- `job_type`
- `contractor_tier`
- `hourly_min`
- `hourly_max`
- `fixed_amount`
- `raw_id`

stderr는 diagnostics 전용이며 raw cookie/session/proxy/token 값을 포함하면 안 됩니다.

## 개발 품질 게이트

구현 완료를 주장하기 전에 `make quality`와 `make smoke`의 fresh output을 확인해야 합니다.

```bash
make quality
make smoke
```

`make quality`는 아래 명령을 순서대로 실행합니다.

```bash
ruff format --check .
ruff check .
mypy src
pytest
```

Live smoke는 다음 조건을 만족할 때만 성공으로 보고합니다.

- `UPWORK_COLLECTOR_LIVE=1`로 명시적으로 활성화
- 실제 Upwork 요청 수행
- nonzero JSONL job record 출력
- 기본 실행 기준 최대 50개 출력
- secret leakage 없음

## Secret 정책

아래 값은 commit, fixture, docs example, stdout, stderr, logs, API payload에 들어가면 안 됩니다.

- real cookie
- bearer token
- session ID
- credential 포함 proxy URL
- private Upwork response
- account-specific request header/sample

Live용 local file은 `.gitignore`에 의해 제외되어야 합니다.
