# Contributing

Keep changes small, testable, and aligned with the Docker/MCP-first data engine
scope.

## Project scope

Good contribution areas:

- Docker runtime, MCP tools, SQLite persistence, ingestion, analytics, tests, and docs.
- Secret-safe collection normalization and deduplication.
- Agent-facing lookup summaries over already-collected data.

Out of scope unless the project direction changes first:

- backend ranking engines, proposal/message generation, auto-apply flows, notifications, or UI;
- cookie, session, proxy, credential-bypass, or unsafe collection guidance;
- persistence of upstream private GraphQL envelopes, raw snapshots, or per-job observation logs.

## Local setup

```bash
cp .env.example .env
docker compose up -d --build
docker compose ps
```

Use Docker/MCP for normal operation. Direct `uv run work-feed ...` commands are
for local debugging and maintenance.

## Verification

Run the offline checks before opening a pull request:

```bash
uv run --extra dev ruff format --check .
uv run --extra dev ruff check .
uv run --extra dev mypy src
uv run --extra dev lint-imports
uv run --extra dev pytest -q
uv run --extra dev pytest --cov --cov-report=term-missing --cov-fail-under=80 -q
```

These checks cover formatting, linting, strict typing, import architecture contracts,
tests, and the conservative 80% coverage gate. CI also runs fixture smoke and e2e
smoke flows on pull requests and pushes.

Do not run live Upwork collection as part of normal verification. If live
evidence is explicitly requested, report it separately from fixture/local
contract evidence.

## Pull requests

Include:

- what changed and why;
- relevant tests or why tests are not useful;
- docs updates when setup, behavior, release, or agent usage changes;
- confirmation that no secrets, session data, proxy details, bypass
  instructions, or runtime artifacts are committed.

For vulnerabilities or sensitive reports, follow `SECURITY.md`.
