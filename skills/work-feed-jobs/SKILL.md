---
name: work-feed-jobs
description: Query and summarize already-collected Upwork jobs from the work-feed MCP data engine. Use when the user asks for recent collected jobs, 수집된 공고 조회, python/scraping/skill-based job search, 추천 후보, 지원할 만한 공고 후보, work-feed jobs, Upwork collected jobs, job discovery DB, specific job_id details, or collector/run status. This skill only reads collected data via MCP tools; it does not run live collection, scraping, scheduler setup, Docker operations, proposal/message writing, auto-apply, or backend ranking.
---

# Work Feed Jobs

Use work-feed MCP tools to read **already-collected** Upwork jobs and produce compact lookup or candidate summaries. Treat collection as app-owned: a Docker worker already collects data locally or in the deployment environment, and this skill only queries what exists.

## Hard boundaries

- Prefer work-feed MCP tools before any local DB or shell fallback.
- Do not run live scraping, live collection, scheduler setup, deployment, Docker operations, or worker control.
- Do not write proposals, messages, cover letters, or auto-apply flows. If asked, say this skill is limited to helping select candidate jobs.
- Do not create or describe backend ranking engines. Simple sorting and short match reasons over retrieved rows are allowed.
- Do not include Upwork cookie, session, proxy, bypass, credential, or access-control guidance.
- Do not invent missing fields. Use `unknown` or `null` when client or job data is absent.
- Do not overstate fit or job details; base every reason on fields returned by the MCP tools.

## Tool decision tree

Use the narrowest MCP tool that satisfies the request:

1. **No filters / recent jobs**: call `jobs_recent`.
2. **Keyword, title, skill, or stack filter**: call `jobs_search`. Map free-text terms to `title` for broad title search; map a single normalized skill name to `skill` for exact skill search. For multi-term requests such as `python scraping`, run one or more focused searches rather than passing the full phrase as one exact skill.
3. **Specific `job_id`**: call `jobs_get` for details.
4. **Candidate/recommendation request**: retrieve with `jobs_search` when terms exist, otherwise `jobs_recent`; then rank only the returned rows by obvious matches such as keyword/skill overlap, freshness, and budget/hourly presence.
5. **Collector or ingestion status**: call `collector_status`; use `runs_recent` for recent run history.
6. **MCP unavailable or tool failure**: clearly state that a work-feed MCP connection is required, then stop or offer to retry once connected.

If multiple intents appear, answer the data lookup first and keep status/diagnostics separate.

## Output rules

- Summarize the top 5-10 items; do not dump large raw result sets.
- Preserve URLs exactly as returned.
- Keep budget/hourly concise: fixed budget, hourly range, or `unknown`.
- Include `posted_at` when available; otherwise use the returned first-seen/created timestamp only if clearly labeled.
- Keep reasons short and factual: matched keyword, matched skill, budget/hourly signal, freshness, or missing exclusion terms.

### Basic lookup format

```text
최근/검색 공고 N개

1. <title>
   job_id: <job_id>
   skills: <skill1>, <skill2> | unknown
   budget/hourly: <fixed budget or hourly range or unknown>
   posted_at: <posted_at or unknown>
   url: <url or unknown>
```

### Candidate format

```text
추천 후보 N개

1. <title>
   rank: 1
   job_id: <job_id>
   match reason: <short factual reason>
   skills: <skill1>, <skill2> | unknown
   budget/hourly: <fixed budget or hourly range or unknown>
   posted_at: <posted_at or unknown>
   url: <url or unknown>
```

### Status format

```text
수집 상태
- collector: <status or unknown>
- last run: <timestamp/status or unknown>
- recent runs: <short summary from runs_recent if requested or useful>
```

## Empty or weak results

When no jobs match:

- Say no collected jobs matched the current condition.
- Suggest 2-3 safer relaxed alternatives, such as broader keyword, fewer skills, no budget filter, or recent jobs.
- Do not offer to run live collection from this skill.

Example:

```text
수집된 데이터에서 `python playwright scraping` 조건과 일치하는 공고를 찾지 못했습니다.
조건을 `python`, `scraping`, 또는 `playwright` 중 하나로 완화해 다시 조회할 수 있습니다.
```

## Refusals / scope redirects

- Proposal request: “이 skill은 지원 문안/proposal/message 작성 범위를 다루지 않습니다. 대신 지원 후보 공고를 고르는 데 필요한 요약은 도와드릴 수 있습니다.”
- Live collection request: “이 skill은 이미 수집된 데이터 조회 전용입니다. live collection 실행은 범위 밖입니다.”
- Scheduler/Docker request: “이 skill은 scheduler, Docker 운영, 배포 설정을 하지 않습니다. 수집 상태 조회까지만 가능합니다.”
- MCP missing: “work-feed MCP 연결이 필요합니다. `jobs_recent`, `jobs_search`, `jobs_get`, `runs_recent`, `collector_status` 도구가 연결된 환경에서 다시 실행해야 합니다.”

## Example requests and responses

Use these as response shapes; replace placeholder values only with fields returned by MCP tools.

### “최근 공고 보여줘”

Call `jobs_recent`, then respond:

```text
최근 수집 공고 5개

1. <title from row>
   job_id: <job_id>
   skills: <skills or unknown>
   budget/hourly: <budget/hourly or unknown>
   posted_at: <posted_at or unknown>
   url: <url or unknown>
```

### “python 공고 찾아줘”

Call `jobs_search` with `skill="python"` when the user clearly means the Python skill, or `title="python"` for a broad title keyword search, then respond:

```text
`python` 검색 결과 5개

1. <title>
   job_id: <job_id>
   skills: <returned skills, for example python if present>
   budget/hourly: <budget/hourly or unknown>
   posted_at: <posted_at or unknown>
   url: <url or unknown>
```

### “추천 후보 뽑아줘: python scraping”

Call focused searches such as `jobs_search(skill="python")`, `jobs_search(skill="scraping")`, or title searches for the individual terms; merge/deduplicate the returned rows before ranking, then respond:

```text
추천 후보 5개

1. <title>
   rank: 1
   job_id: <job_id>
   match reason: returned title/skills matched requested term(s); posted_at is recent if available.
   skills: <skills or unknown>
   budget/hourly: <budget/hourly or unknown>
   posted_at: <posted_at or unknown>
   url: <url or unknown>
```

### “job_id abc123 자세히 보여줘”

Call `jobs_get` for `abc123`, then respond:

```text
공고 상세
- title: <title>
- job_id: abc123
- skills: <skills or unknown>
- budget/hourly: <budget/hourly or unknown>
- posted_at: <posted_at or unknown>
- client: <client fields or unknown/null>
- url: <url or unknown>
```

### “수집기 상태 어때?”

Call `collector_status`; call `runs_recent` if recent run detail is requested or needed, then respond:

```text
수집 상태
- collector: <status>
- last run: <last run timestamp/status or unknown>
- recent runs: <brief run summary or omitted if not fetched>
```
