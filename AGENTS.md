# AGENTS.md — upwork-collector

## 역할과 의도

이 저장소는 `upwork-collector`의 canonical 구현 대상입니다. 목표는 Python-only Upwork scraper core를 만들고, 결과를 downstream에서 소비 가능한 JSONL로 출력하는 것입니다.

구현 판단의 기준은 아래 repo-local 문서입니다.

- `docs/PRD.md`
- `docs/TEST_PLAN.md`
- `docs/adr/0001-python-jsonl-collector.md`

`.omx/` 문서는 원본 계획 provenance이며, 구현 중 요구사항 충돌이 있으면 `docs/` 문서를 우선 확인하고 `.omx/` 원본으로 근거를 추적합니다.

## 범위

해야 할 일:

- Python package `upwork_collector`
- CLI entrypoint `upwork-collector`
- fixture 기반 deterministic collection
- 명시적 opt-in live smoke
- Upwork GraphQL request/response 처리
- normalized JSONL job schema
- typed error taxonomy와 stable exit code
- credential/session/proxy redaction
- pytest, ruff, mypy 품질 체계

하지 말아야 할 일:

- Swift/UI/watcher 구현
- upfeed scheduler/API/storage 통합
- Go-native collector
- SQLite 또는 기본 durable local state
- JSON snapshot writer
- daemon/scheduler ownership
- recommendation/scoring/notification/product judgment
- proxy acquisition 문서 또는 access-control 우회 playbook

## 보안/secret 정책

절대 commit하거나 출력하지 말 것:

- cookie
- bearer token
- session ID
- credential 포함 proxy URL
- Webshare/private proxy 정보
- private Upwork response
- account-specific sample/header

stdout은 JSONL job record only입니다. stderr는 diagnostics only이며 secret은 반드시 redaction해야 합니다.

Fixtures는 synthetic 또는 sanitized여야 합니다.


## 테스트 정책

Mock/fake transport로 Upwork 수집 성공을 주장하지 않습니다. Local tests는 순수 로직과 계약(JSONL serialization, CLI arguments, exit codes, redaction, parser/normalizer behavior)만 검증합니다.

실제 collector 성공은 live E2E/smoke에서만 인정합니다. Live 테스트는 명시적 opt-in이 필요하며, 실제 Upwork 응답과 nonzero JSONL job records가 있어야 합니다.

## 구현 순서

TDD 우선:

1. error/exit-code tests
2. model/normalization tests + sanitized fixtures
3. CLI fixture stdout/stderr tests
4. credential redaction tests
5. GraphQL/parser contract tests. Mock/fake transport로 수집 성공을 주장하지 않는다.
6. 최소 구현
7. README/docs 정리
8. 품질 게이트와 local contract smoke

## 완료 전 필수 검증

아래 명령을 실행하고 결과를 읽은 뒤에만 완료를 주장합니다.

```bash
ruff format --check .
ruff check .
mypy src
pytest
```

CLI가 생긴 뒤 local contract smoke도 실행합니다.

```bash
upwork-collector collect --fixture tests/fixtures/visitor_job_search_response.json > /tmp/upwork-collector-fixture.jsonl
python -c 'import json,sys; [json.loads(line) for line in sys.stdin if line.strip()]' < /tmp/upwork-collector-fixture.jsonl
```

Live smoke는 별도 opt-in이며, 실행하지 않았다면 `not run`으로 보고합니다.
