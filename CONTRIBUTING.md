# Contributing

Thanks for improving `work-feed-mcp`. Keep changes small, testable, and aligned with the Docker/MCP-first data engine scope.

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
make up
make status
```

Use Docker/MCP for normal operation. Direct `uv run work-feed ...` commands are for local debugging and maintenance.

## Verification

Run the offline checks before opening a pull request:

```bash
make quality
make architecture
make coverage
make smoke
make e2e-smoke
```

`make quality` is the normal PR gate: it checks formatting, linting, strict typing, import architecture contracts, and tests. `make architecture` runs the import-boundary contracts by themselves when you are changing package dependencies. `make coverage` runs the pytest coverage gate; the threshold starts conservatively at 80% so contributors improve coverage without chasing an aggressive target.

Do not run live Upwork collection as part of normal verification. If live evidence is explicitly requested, report it separately from fixture/local contract evidence.

## Pull requests

Please include:

- what changed and why;
- relevant tests or why tests are not useful;
- docs updates when setup, behavior, release, or agent usage changes;
- confirmation that no secrets, session data, proxy details, bypass instructions, or runtime artifacts are committed.

Be respectful and constructive in issues and reviews. For vulnerabilities or sensitive reports, follow `SECURITY.md`.
