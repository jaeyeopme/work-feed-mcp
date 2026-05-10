# Test Spec: upwork-collector Python Scraper Core

## Status

- Workflow: `$ralplan`
- Artifact type: test plan only
- Implementation status: **not approved / not started**
- Canonical implementation target for future work: `/Users/jaeyeop/Workspace/upwork-collector`

## Test Strategy

The implementation must be test-first. Default validation is deterministic, local, fixture-based, and network-free. Live validation is separate, explicit, and never a substitute for unit/fixture tests.

Quality commands for future implementation:

```bash
ruff format --check .
ruff check .
mypy src
pytest
```

## Test Pyramid

1. Unit tests for pure functions and typed models.
2. Contract tests for CLI streams, JSONL schema, and exit codes.
3. Fixture integration tests using sanitized GraphQL response files.
4. Opt-in live smoke tests gated by command and environment.
5. Secret-leak/static checks before claiming completion.

## Fixture Requirements

Fixtures must be synthetic or sanitized and must not contain:

- cookies
- bearer tokens
- session IDs
- proxy URLs
- account-specific private data
- reusable request headers tied to a real account
- raw private samples

Required fixtures:

- `tests/fixtures/visitor_job_search_response.json`: representative GraphQL response with at least two job results.
- `tests/fixtures/malformed_response.json`: response missing the expected `data.search.universalSearchNuxt.visitorJobSearchV1.results` path.
- Optional targeted fixtures for missing optional budget/hourly fields, missing required identity fields, GraphQL `errors`, blocked, and rate-limited responses.

## Normalization Tests

File: `tests/test_normalize.py`

### Cases

1. `test_normalizes_representative_graphql_response`
   - Given sanitized `visitor_job_search_response.json`.
   - When normalized.
   - Then each job has required fields:
     - `source == "upwork"`
     - `id`
     - `title`
     - `description`
     - `url`
     - `skills` list
   - And optional fields are present with values or `None`:
     - `posted_at`
     - `job_type`
     - `contractor_tier`
     - `hourly_min`
     - `hourly_max`
     - `fixed_amount`
     - `raw_id`

2. `test_missing_optional_fields_are_safe`
   - Missing budget/hourly/contractor tier fields normalize to `None` or empty safe defaults.
   - No exception for optional omissions.

3. `test_missing_required_identity_fails_closed`
   - Missing both raw result `id` and nested `job.cipherText`/`ciphertext` fails with typed schema/upstream temporary error.

4. `test_malformed_response_shape_fails_closed`
   - Missing expected GraphQL path maps to typed error for exit code `30`.

5. `test_graphql_errors_fail_closed`
   - Response with GraphQL `errors` does not emit partial successful JSONL unless a future explicit partial policy is approved.

## Models Tests

File: `tests/test_models.py` if model behavior is nontrivial; otherwise covered by normalization tests.

### Cases

- `Job` serialization emits JSON-compatible dicts only.
- `skills` is always a list.
- Numeric fields are numbers or `None`.
- Datetime fields are strings or `None`, not `datetime` objects in JSONL output.

## Credentials and Redaction Tests

File: `tests/test_credentials.py`

### Cases

1. `test_fixture_mode_does_not_require_credentials`
   - Fixture mode loads no live credential/session values.

2. `test_live_mode_missing_credentials_maps_to_credential_required`
   - Live mode without required local credential/session state raises typed credential error.
   - CLI maps it to exit code `10`.

3. `test_local_file_reference_can_be_loaded_without_printing_value`
   - Given a temp cookie/session file.
   - Loader returns an internal credential object.
   - String/repr/diagnostics do not contain the raw value.

4. `test_redacts_cookie_bearer_proxy_and_env_values`
   - Redaction masks:
     - cookie strings
     - bearer tokens
     - proxy URLs with credentials
     - session file content
     - matching env var values

5. `test_exceptions_are_redacted`
   - Exceptions wrapping HTTP/client failures must not include raw credential/session/proxy material.

## CLI Fixture Contract Tests

File: `tests/test_cli_fixture.py`

### Cases

1. `test_fixture_collect_emits_jsonl_stdout_only`
   - Run `upwork-collector collect --fixture tests/fixtures/visitor_job_search_response.json` or module equivalent.
   - Assert exit code `0`.
   - Assert stdout has one JSON object per line.
   - Assert every line parses as JSON.
   - Assert stderr contains no job JSON records.

2. `test_diagnostics_do_not_pollute_stdout`
   - Force a harmless diagnostic.
   - Assert stdout remains JSONL only.

3. `test_stderr_never_contains_secret_like_fixture_values`
   - Inject fake secret env values.
   - Assert stderr does not contain them.

4. `test_invalid_cli_options_exit_usage_error`
   - Incompatible `--fixture` and `--live` options or invalid page size maps to exit code `2`.

5. `test_fixture_mode_does_not_create_state_files`
   - Run fixture CLI in a temp cwd/home.
   - Assert no SQLite DB, snapshot JSON, scheduler state, daemon state, or hidden durable project state is created by default.

## Exit-Code Tests

File: `tests/test_error_exit_codes.py`

Required mapping:

| Scenario | Expected code |
|---|---:|
| Success | 0 |
| Invalid arguments | 2 |
| Missing/invalid live credential/session/token/cookie | 10 |
| Upstream blocked/forbidden/access-denied | 20 |
| Upstream rate limited/throttled | 21 |
| GraphQL errors, malformed shape, timeout, retryable upstream failure | 30 |
| Unexpected local bug/invariant failure | 40 |

### Cases

- Unit-test typed error to exit-code function.
- CLI-level tests for at least usage, credential, schema/temp failure, and internal failure.
- Transport fake tests for blocked and rate-limited responses.

## Transport Contract Tests

File: `tests/test_transport_contract.py`

### Cases

1. `test_transport_is_replaceable_with_fake`
   - GraphQL/client code accepts a fake transport; default tests do not touch network.

2. `test_graphql_endpoint_contract`
   - Request builder targets `https://www.upwork.com/api/graphql/v1`.

3. `test_graphql_request_variables_contract`
   - Request variables include paging offset/count and optional user query.
   - Budget filters are not invented unless verified; if present, client-side filtering must be separately tested and not required for MVP.

4. `test_visitor_token_cookie_is_consumed_without_logging`
   - Fake bootstrap response with `visitor_gql_token` is accepted internally.
   - Token value is absent from diagnostics, reprs, and exceptions.

5. `test_default_tests_block_network`
   - Monkeypatch or fake transport ensures accidental live HTTP calls fail the test.

## GraphQL Tests

File: `tests/test_graphql.py` if separate from transport tests.

### Cases

- GraphQL query document includes required fields needed by normalizer.
- Extractor reads `data.search.universalSearchNuxt.visitorJobSearchV1.results`.
- Extractor handles `paging` metadata without requiring persistence.
- GraphQL `errors` raise typed upstream/schema error.

## Live Smoke Tests

File: `tests/test_live_smoke.py`

### Gating

Live tests must be skipped unless all required live gates are present:

- Explicit `live-smoke` command or live test invocation.
- `UPWORK_COLLECTOR_LIVE=1`.
- Required local credential/session references only when the selected transport mode requires them.
- Explicit test marker such as `pytest -m live` if markers are configured.

### Cases

1. `test_live_smoke_requires_explicit_enablement`
   - Without `UPWORK_COLLECTOR_LIVE=1`, test is skipped or asserts live command refuses safely.

2. `test_live_missing_credentials_is_credential_required_when_selected_mode_requires_them`
   - With live gate enabled but no required local credential/session for a credential/session-backed mode, command exits `10` and prints redacted diagnostics.
   - Visitor-token bootstrap mode may proceed without credential/session material if it can do so safely.

3. `test_live_collects_nonzero_jobs_when_credentials_available`
   - Only runs when credentials are present.
   - Performs real Upwork request.
   - Requires exit code `0` and nonzero JSONL job records.
   - Captures evidence separately from fixture success.

## Secret-Leak Verification

Before completion, run a search over the new project for likely secret material and forbidden state artifacts.

Suggested checks for future implementation:

```bash
find . -name '*.sqlite' -o -name 'snapshot-*.json'
grep -RInE 'visitor_gql_token|Bearer [A-Za-z0-9._-]+|https?://[^[:space:]]+:[^[:space:]]+@|WEBSHARE|session|cookie' . \
  --exclude-dir=.git --exclude-dir=.venv
```

These checks are not sufficient proof by themselves; they are a final guard in addition to redaction tests and fixture review.

## TDD Implementation Order

1. Write `errors.py` tests and exit-code mapping tests.
2. Write `models.py`/normalization tests using sanitized fixtures.
3. Write CLI fixture stdout/stderr tests.
4. Write credential redaction tests.
5. Write transport/GraphQL fake tests.
6. Implement minimal code to pass those tests.
7. Add README and verify docs do not contain secret material or live-success overclaims.
8. Run quality gate.
9. Run fixture smoke.
10. Run live smoke only if explicitly enabled and credentials are available.

## Acceptance Evidence Required Before Claiming Implementation Complete

Default implementation completion requires:

- `ruff format --check .` passed.
- `ruff check .` passed.
- `mypy src` passed.
- `pytest` passed without network.
- Fixture CLI smoke passed.
- Secret-leak/static checks reviewed.
- Confirmation that no SQLite/snapshot/scheduler/daemon state is created by default.
- Live smoke status reported as one of:
  - `not run: no explicit live approval`, or
  - `not run: selected transport required credentials/session material that was unavailable`, or
  - `failed: <redacted reason>`, or
  - `passed: real Upwork response, nonzero JSONL jobs, no secret leakage observed`.

## Stop Condition

This test spec is complete when reviewed with the paired PRD and Critic approves it as testable. No implementation should begin from this artifact until the user approves a follow-up execution mode.
