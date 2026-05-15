# AGENTS.md — upwork data engine

## Role and intent

This repository is a Docker/MCP-first local data engine for the Upwork job discovery pipeline. Agents are expected to consume the MCP tools for job lookup, collection status, and safe collector control. Keep responsibilities separated by app layer:

- `src/upwork_app/integrations/upwork`: Upwork/fixture collection, credential redaction, GraphQL transport, and normalized job records.
- `src/upwork_app/services`: application use cases for collection, ingestion, and analytics orchestration.
- `src/upwork_app/repositories` and `src/upwork_app/db`: SQLite persistence, schema, and query helpers.
- `src/upwork_app/domain`: collector-record validation and canonical data contracts.
- `src/upwork_app/runtime` and `src/upwork_app/mcp_server`: Docker worker runtime and agent-facing MCP server.
- `src/upwork_app/cli`: stable local/debug commands.

The implemented app path is `integrations/upwork → services/scheduled_collection → SQLite → mcp_server`, with CLI commands kept as local/debug and native-operation entrypoints.

## Boundaries

Keep Upwork collection dumb and secret-safe:

- normalized job records only; no upstream private GraphQL envelopes in persisted raw records.
- diagnostics must redact credential/session/proxy/token material.
- no backend ranking, auto-apply, proposal/message generation, notifications, or UI in the core data engine.
- recommendation/ranking belongs in the consuming agent layer unless explicitly promoted later.
- no proxy acquisition docs or access-control bypass playbooks.

SQLite persistence belongs in ingestion/db/repository code. Analytics and MCP reads SQLite only. Docker Compose is the primary runtime: the worker owns recurring collection and the MCP server exposes agent-facing tools.

Use `docs/LLM_CONTEXT.md` and `docs/contracts/job-jsonl.md` for detailed context.

## Verification

For normal changes, run from repo root:

```bash
make quality
make smoke
make e2e-smoke
```

For duplicate checks, run:

```bash
npx jscpd --reporters ai --gitignore --min-lines 10 \
  --ignore "**/.venv/**,**/.mypy_cache/**,**/.pytest_cache/**,**/.ruff_cache/**,**/__pycache__/**,**/*.egg-info/**,**/uv.lock,.omx/**" .
```

For live evidence, run only with explicit opt-in:

```bash
make live-smoke QUERY="python"
```

Report live status separately from fixture/local contract evidence.
