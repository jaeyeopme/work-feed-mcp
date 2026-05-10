# upwork-analytics

`upwork-analytics`는 `upwork-ingest`가 만든 SQLite DB를 읽어 기본 집계/조회 결과를 JSON으로 출력합니다.

이 패키지는 SQLite-only analytics layer입니다.

- collector를 호출하지 않습니다.
- JSONL을 직접 파싱하지 않습니다.
- DB record를 mutate하지 않습니다.
- ranking, scoring, auto-apply, message generation을 하지 않습니다.

## CLI

```bash
upwork-analytics query summary --db .local/upwork.sqlite
upwork-analytics query skills --db .local/upwork.sqlite
upwork-analytics query jobs --db .local/upwork.sqlite --skill python
upwork-analytics query budgets --db .local/upwork.sqlite
upwork-analytics query runs --db .local/upwork.sqlite
upwork-analytics query clients --db .local/upwork.sqlite
```

## Query 범위

- `summary`: jobs/runs/observations/raw_records count
- `skills`: skill frequency
- `jobs`: skill/title filter 기반 job 목록
- `budgets`: fixed/hourly/unknown budget distribution
- `runs`: ingest run metadata
- `clients`: 조건부 client dimension bucket

## Client analytics 규칙

Client dimension은 SQLite `jobs` table에 해당 column이 있을 때만 집계합니다.

없는 field는 title/description에서 추론하지 않고 `unknown`/`null`로 반환합니다. 따라서 현재 collector contract에 rich client field가 없더라도 analytics는 데이터를 날조하지 않습니다.

## 검증

```bash
ruff format --check .
ruff check .
mypy src
pytest -q
```
