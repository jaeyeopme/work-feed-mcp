# PRD: upwork-collector Python Scraper Core

## Status

- Workflow: `$ralplan`
- Artifact type: planning only
- Implementation status: **not approved / not started**
- Canonical implementation target: `/Users/jaeyeop/Workspace/upwork-collector`
- Planning workspace: `/Users/jaeyeop/Workspace/up-cli`

## Grounding Evidence

- The requested planning workspace `/Users/jaeyeop/Workspace/up-cli` currently has no `AGENTS.md` and no `.omx/specs/deep-interview-agent-misalignment-control.md` file.
- The matching Deep Interview spec was found at `/Users/jaeyeop/Workspace/upfeed/.omx/specs/deep-interview-agent-misalignment-control.md` and used as the planning authority.
- The target project `/Users/jaeyeop/Workspace/upwork-collector` does not exist yet and must be created there, not under `upfeed` or the current `up-cli` directory.
- Legacy reference scraper: `/Users/jaeyeop/Workspace/upwork-scraper/scraper.py`.
- Legacy scraper evidence to keep as reference only:
  - `curl_cffi.requests` browser-like HTTP stack.
  - visitor token bootstrap from `https://www.upwork.com/` via `visitor_gql_token` cookie.
  - GraphQL POST to `https://www.upwork.com/api/graphql/v1`.
  - response traversal through `search.universalSearchNuxt.visitorJobSearchV1.results`.
- Legacy scraper behavior explicitly not ported into MVP:
  - SQLite persistence.
  - JSON snapshot writing.
  - standalone durable state ownership.
  - scheduler/daemon ownership.
  - random sleep orchestration and thread-pool ownership as product behavior.
  - proxy-list acquisition or reusable access-control/circumvention playbooks.

## Product Goal

Create a clean Python package and CLI named `upwork-collector` that collects Upwork job search results, normalizes them, and emits one normalized job JSON object per stdout line for downstream consumers.

This MVP is a scraper core only. It is not a Swift app, UI, watcher, upfeed scheduler integration, Go-native collector, daemon, storage engine, or recommendation product.

## RALPLAN-DR Summary

### Principles

1. **Pure collector boundary**: Python owns only live scraping transport, GraphQL request/response handling, normalization, error mapping, and CLI JSONL output.
2. **TDD-first**: fixture, contract, and failure-mode tests are written before implementation behavior is claimed complete.
3. **Secret-safe by construction**: credential/session/proxy material stays local and must not appear in commits, fixtures, stdout, stderr, docs examples, or API payloads.
4. **Machine contract first**: stdout is JSONL records only; stderr is diagnostics only; exit codes are stable and tested.
5. **Fixture evidence is not live evidence**: default tests prove local behavior; opt-in live smoke proves real network behavior only when explicitly run.

### Decision Drivers

1. Prevent prior scope drift into Swift/UI/watcher/upfeed scheduler/Go-native architecture.
2. Preserve useful legacy Upwork transport knowledge without inheriting SQLite/snapshots/durable state.
3. Make correctness testable through typed models, deterministic fixtures, redaction tests, and exact exit-code mapping.

### Viable Options

#### Option A — New clean Python package at canonical target path

Pros:
- Matches the Deep Interview spec.
- Keeps transport/GraphQL/normalization boundaries testable.
- Avoids upfeed scheduler/API/storage concerns.
- Supports future integration through JSONL without coupling.

Cons:
- Requires new scaffolding.
- Live parity with the legacy scraper must be proven later through opt-in smoke.

#### Option B — Thin wrapper around legacy `scraper.py`

Pros:
- Fastest route to reuse the known live request path.
- Minimizes initial unknowns around Upwork request details.

Cons:
- High risk of carrying SQLite, snapshots, proxy pool state, random sleeps, and standalone ownership into the MVP.
- Harder to enforce stdout/stderr purity and secret redaction.
- Conflicts with TDD-first clean architecture.

#### Option C — Build inside `upfeed`

Pros:
- Close to a likely future consumer.

Cons:
- Violates the requested new target path.
- Reintroduces scheduler/API/storage scope drift.
- Makes fixture/live collector evidence harder to separate from daemon behavior.

### Decision

Choose **Option A**: a clean Python package at `/Users/jaeyeop/Workspace/upwork-collector`, using `scraper.py` only as reference evidence for token bootstrap, GraphQL endpoint/query shape, and raw response structure.

## MVP Scope

### In Scope

Project layout:

```text
/Users/jaeyeop/Workspace/upwork-collector/
  pyproject.toml
  README.md
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

Functional scope:

- CLI entrypoint, preferably `upwork-collector`.
- Fixture mode for deterministic local JSONL emission.
- Live mode as explicit opt-in.
- Browser-like transport abstraction, with implementation details hidden in `transport.py`.
- Upwork GraphQL request builder and parser in `graphql.py`.
- Normalization of raw Upwork job result nodes into stable `Job` DTOs.
- Credential/session loading from local environment or local file references.
- Redaction for credential/session/proxy-like values in diagnostics and exceptions.
- Typed errors and numeric exit-code mapping.
- README documenting setup, quality commands, fixture vs live evidence, CLI usage, and secret-handling constraints.

### Out of Scope

- Swift.
- UI.
- Watcher app behavior.
- upfeed scheduler/API/storage changes.
- Go-native Upwork collector.
- SQLite.
- JSON snapshots.
- Default local durable state.
- Recommendation, fit scoring, user-facing labels, notification policy, or product judgment.
- Credential/session material in fixtures, docs, payloads, stdout, stderr, or commit history.
- Proxy acquisition docs or reusable access-control/circumvention playbooks.

## CLI Contract

### Commands

The exact implementation may use `argparse`, but must expose these behaviors:

```bash
upwork-collector collect --fixture tests/fixtures/visitor_job_search_response.json
upwork-collector collect --query "python" --max-pages 1 --page-size 10 --live
UPWORK_COLLECTOR_LIVE=1 upwork-collector live-smoke --query "python" --max-pages 1 --page-size 10
```

Equivalent `python -m upwork_collector ...` commands are acceptable if documented.

### Options

- `collect`
  - `--fixture <path>`: read sanitized fixture response; no credentials; no network.
  - `--live`: enable real Upwork network transport; absent by default.
  - `--query <text>`: optional Upwork search query.
  - `--max-pages <int>`: default `1` for MVP.
  - `--page-size <int>`: default `10` for MVP; bounded by implementation.
  - `--output jsonl`: default and only MVP output format.
- `live-smoke`
  - Always live/opt-in.
  - Must require both the explicit `live-smoke` command and `UPWORK_COLLECTOR_LIVE=1`.
  - Visitor-token bootstrap is allowed as an internal transport mode when it works without credential/session material.
  - Credential/session-backed transport is allowed only through local references when required by the selected transport mode.
  - Must fail or skip safely when the selected transport mode requires credential/session prerequisites and they are absent.

### Stream Contract

- stdout: only normalized job JSON objects, one per line.
- stderr: diagnostics, warnings, and errors only.
- No JSON job records on stderr.
- No diagnostics on stdout.
- No credential/session/proxy values on either stream.

## JSONL Job Schema

Each stdout line is a JSON object.

Required fields:

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

Optional nullable fields:

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

URL construction should prefer the legacy `cipherText`/ciphertext field when present. If the canonical permalink format is not verified during fixture implementation, the normalizer must either build a deterministic Upwork job URL from available identity data or fail closed for missing required `url` rather than emitting ambiguous records.

## Exit-Code Taxonomy

Numeric codes are part of the CLI contract and must be tested.

| Code | Name | Meaning |
|---:|---|---|
| 0 | success | One or more requested operations completed successfully. Fixture success may emit zero or more records only if the fixture intentionally contains zero jobs; live success requires nonzero records. |
| 2 | usage_error | Invalid CLI arguments or incompatible options. |
| 10 | credential_required | Missing/invalid credential, session, token, cookie, or required local credential reference for live mode. |
| 20 | upstream_blocked | Upwork returned a block/forbidden/access-denied style response. |
| 21 | rate_limited | Upwork returned a rate-limit/throttle response. |
| 30 | upstream_schema_or_temporary_failure | GraphQL errors, malformed/unexpected upstream shape, missing required raw fields, timeout, or retryable upstream failure. |
| 40 | internal_failure | Unexpected local bug or invariant violation. |

## Credential and Session Boundary

Allowed:

- Use visitor-token bootstrap as an internal live transport mode when it works without local credential/session material.
- Read local references from environment variables when the selected transport mode requires them, such as:
  - `UPWORK_COLLECTOR_SESSION_FILE`
  - `UPWORK_COLLECTOR_COOKIE_FILE`
  - `UPWORK_COLLECTOR_PROXY_URL`
  - `UPWORK_COLLECTOR_LIVE=1`
- Read local files that are `.gitignore`d by the new project.
- Report credential status metadata such as `missing`, `loaded`, `redacted`, or `invalid`.

Forbidden:

- Committing real cookies, bearer tokens, proxy URLs, sessions, Webshare URLs, private responses, or account-specific samples.
- Printing raw credential/session/proxy material in stdout/stderr/logs/exceptions.
- Documenting reusable bypass instructions, proxy acquisition flows, or access-control circumvention playbooks.
- Adding credential/session values to API payloads or fixture files.

## Transport Boundary

- `transport.py` owns HTTP client setup and browser-like request behavior.
- `graphql.py` owns endpoint URL, query document, request variables, and response extraction.
- `cli.py` orchestrates commands only; it must not own Upwork request internals or persistence.
- `normalize.py` maps raw job result nodes to typed models; it must not perform network or state writes.
- Default tests must replace live transport with fixture/fake transport and must not perform network calls.

## Acceptance Criteria

1. Project scaffold exists at exactly `/Users/jaeyeop/Workspace/upwork-collector`.
2. `pyproject.toml` defines pytest, ruff, and mypy quality commands/configuration.
3. `README.md` documents setup, CLI, TDD workflow, fixture validation, live validation, and secret boundaries.
4. Fixture CLI mode emits valid JSONL records to stdout and diagnostics only to stderr.
5. Normalization maps fixture GraphQL responses to the stable schema.
6. Malformed fixture responses fail closed with typed error mapped to code `30` unless a more specific code applies.
7. Missing live credential/session prerequisites map to code `10`.
8. Rate-limit and blocked responses map to codes `21` and `20` respectively.
9. Default tests run without network and without credentials.
10. Live smoke is opt-in and cannot be described as successful unless it performs a real Upwork request and emits nonzero JSONL job records.
11. No SQLite database, JSON snapshot, scheduler, daemon state, Swift/UI/watcher, or Go-native collector code is created by default.
12. No committed fixture, doc, test, payload, stdout, or stderr content contains raw credential/session/proxy material.

## Verification Commands for Future Implementation

Default quality gate:

```bash
ruff format --check .
ruff check .
mypy src
pytest
```

Fixture smoke gate:

```bash
upwork-collector collect --fixture tests/fixtures/visitor_job_search_response.json > /tmp/upwork-collector-fixture.jsonl
python -c 'import json,sys; [json.loads(line) for line in sys.stdin if line.strip()]' < /tmp/upwork-collector-fixture.jsonl
```

Live smoke gate, only when explicitly enabled and required live prerequisites are present:

```bash
UPWORK_COLLECTOR_LIVE=1 upwork-collector live-smoke --query "python" --max-pages 1 --page-size 10
```

## ADR

### Decision

Create a new clean Python-only `upwork_collector` package at `/Users/jaeyeop/Workspace/upwork-collector` that emits normalized Upwork jobs as JSONL and keeps fixture validation separate from opt-in live validation.

### Drivers

- Recover the original scraper-core direction after scope drift.
- Preserve useful legacy Python transport knowledge without porting standalone state.
- Provide a TDD-first, typed, testable core suitable for later integration.
- Avoid credential/session leakage.

### Alternatives Considered

- **Directly port/wrap `scraper.py`** — rejected because it risks copying SQLite, snapshots, thread pool orchestration, random sleeps, and proxy state into the MVP.
- **Implement inside upfeed** — rejected because scheduler/API/storage are explicitly deferred and the canonical path is separate.
- **Go-native or Swift/UI implementation** — rejected because the spec explicitly excludes them and Python is the likely best path for browser-like HTTP parity.

### Consequences

- Initial development emphasizes tests, fixtures, CLI contract, and boundaries before live scraping confidence.
- Live behavior must be proven later by opt-in smoke and reported separately from fixture success.
- Future upfeed integration should consume JSONL or package APIs without forcing persistence/scheduler concerns into this project.

### Follow-ups

- During implementation, choose minimal dependency set. `curl_cffi` is likely needed for live transport parity, but should remain isolated behind `transport.py`.
- Treat visitor-token bootstrap and credential/session-backed transport as internal modes; do not document reusable bypass/proxy-acquisition instructions.
- Decide whether proxy configuration is a hidden local transport option or deferred until explicitly requested.
- Add `.gitignore` entries for local session/cookie/proxy files when scaffold is created.

## Available Agent Types and Execution Guidance

### Available agent roster

- `executor`: scaffold and implement package modules and CLI.
- `test-engineer`: author fixture, unit, CLI, redaction, and exit-code tests.
- `code-reviewer`: inspect scope drift, secret handling, stdout/stderr contract, and maintainability.
- `verifier`: run quality gates and collect completion evidence.
- `researcher`: optional for current official package/tooling docs if dependency behavior becomes uncertain.
- `critic`: optional for plan/design challenge if scope expands.
- `architect`: optional for transport/API boundary changes.

### Ralph follow-up

Recommended when a single owner should maintain TDD sequence and verification pressure:

```text
$ralph implement .omx/plans/prd-upwork-collector-python-core-<timestamp>.md and .omx/plans/test-spec-upwork-collector-python-core-<timestamp>.md; stop before any live credential use unless explicitly provided.
```

Suggested reasoning: executor medium, verifier high.

### Team follow-up

Recommended only if parallel throughput is desired:

```text
$team implement the approved upwork-collector Python scraper core plan with disjoint lanes: scaffold/CLI, tests/fixtures, transport/GraphQL, security-review, verification.
```

Suggested lanes:

1. Executor lane: project scaffold, models, errors, CLI skeleton.
2. Test-engineer lane: fixtures, normalize tests, CLI tests, exit-code tests, live smoke gating tests.
3. Executor lane: transport/GraphQL implementation behind interfaces.
4. Code-reviewer lane: secret redaction and non-port/scope audit.
5. Verifier lane: ruff, mypy, pytest, fixture smoke evidence.

Suggested reasoning: executor/test-engineer medium; code-reviewer/verifier high.

### Team verification path

- Verify target path is exactly `/Users/jaeyeop/Workspace/upwork-collector`.
- Verify no Swift/UI/watcher/upfeed/Go-native collector code was added.
- Verify no SQLite/snapshot/default durable state was added.
- Run `ruff format --check .`, `ruff check .`, `mypy src`, `pytest`.
- Run fixture CLI smoke and inspect stdout/stderr separation.
- Search for likely secret patterns before final report.
- Report live smoke as skipped unless explicitly run with evidence.

### Goal-Mode Follow-up Suggestions

- `$ultragoal` — default goal-mode option if the user wants durable sequential tracking from scaffold through verification.
- `$autoresearch-goal` — not recommended for this implementation task unless the next phase becomes research-heavy.
- `$performance-goal` — not applicable unless the next phase becomes speed/throughput optimization.

## Stop Condition

This PRD is complete when paired with the test-spec artifact and approved by Architect/Critic review. Implementation must not begin until the user explicitly approves an execution path.
