# upwork-ingest

`upwork-ingest`는 collector가 출력한 normalized JSONL을 file 또는 stdin으로 읽고 로컬 SQLite DB에 저장합니다.

이 패키지는 persistence만 담당합니다.

- JSONL parsing
- collector contract validation
- SQLite schema creation
- ingest run metadata
- job upsert
- skill normalization
- job observation 기록
- raw normalized collector record provenance 저장

Upwork 호출, collector 실행, ranking, report rendering, client analytics 추론은 담당하지 않습니다.

## CLI

```bash
upwork-ingest ingest --db .local/upwork.sqlite --input jobs.jsonl --query "python"
cat jobs.jsonl | upwork-ingest ingest --db .local/upwork.sqlite --input - --query "python"
```

`--run-id`를 주면 외부에서 정한 run id를 사용합니다. 생략하면 UUID 기반 run id를 생성합니다.

## 저장 데이터

주요 table:

- `ingest_runs`
- `jobs`
- `job_skills`
- `job_observations`
- `raw_records`

`raw_records.payload_json`에는 collector가 stdout으로 출력한 normalized JSON object를 저장합니다. upstream GraphQL response, credential, session token, proxy, private payload는 저장하지 않습니다.

`content_hash`는 canonical payload 기준 SHA-256입니다.

## 검증

```bash
ruff format --check .
ruff check .
mypy src
pytest -q
make smoke
```
