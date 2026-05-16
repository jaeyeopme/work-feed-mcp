# Contributing

Thanks for improving `work-feed-mcp`. This project is a Docker/MCP-first data engine for already-collected Upwork job discovery data, with SQLite as the persistence layer and MCP as the agent-facing interface.

## Scope boundaries

Keep contributions inside the current data-engine contract:

- Docker Compose is the normal runtime.
- MCP tools are the normal agent interface.
- SQLite persistence belongs in `src/work_feed_mcp/db`, `src/work_feed_mcp/repositories`, and service-layer ingestion code.
- Collection should stay dumb, normalized, deduplicated, and secret-safe.
- Do not add backend ranking, built-in recommendation engines, proposal/message generation, auto-apply flows, notifications, or UI unless the project scope is explicitly changed first.
- Do not add cookie, session, proxy, credential-bypass, or unsafe collection guidance.
- Do not persist upstream private GraphQL envelopes, raw snapshots, or per-job observation logs.

## Local setup

```bash
cp .env.example .env
make up
make status
```

Use the Docker/MCP path for normal operation. Direct `uv run work-feed ...` commands are for local debugging and maintenance only.

## Verification

Before opening a pull request, run the offline checks:

```bash
make quality
make smoke
make e2e-smoke
```

These checks are fixture/local contract evidence. Do not run live Upwork collection as part of normal verification. If a maintainer explicitly requests live evidence, run it separately and label it separately from local evidence.

## Pull request expectations

A good pull request includes:

- a concise summary of the user-facing or maintainer-facing change;
- tests or a clear reason why no test is useful;
- documentation updates when behavior, setup, release, or agent usage changes;
- confirmation that no secrets, session data, proxy details, or bypass instructions were added;
- confirmation that generated/runtime files such as `.omx/`, local SQLite files, and logs are not committed.

## Reporting issues

Use the GitHub issue templates for bugs and feature requests. For vulnerabilities or sensitive reports, follow `SECURITY.md` instead of opening a public issue with details.
