# AGENTS.md — upwork data engine

## Role and intent

This repository is a CLI-first local data engine for the Upwork job discovery pipeline. OpenClaw/agents are expected to provide the user interface, orchestration, scheduling assistance, and recommendation layer. Keep responsibilities separated by app layer:

- `src/upwork_app/integrations/upwork`: Upwork/fixture collection, credential redaction, GraphQL transport, and normalized job records.
- `src/upwork_app/services`: application use cases for collection, ingestion, and analytics orchestration.
- `src/upwork_app/repositories` and `src/upwork_app/db`: SQLite persistence, schema, and query helpers.
- `src/upwork_app/domain`: collector-record validation and canonical data contracts.
- `src/upwork_app/cli`: stable local commands for OpenClaw/agent and batch usage.

The implemented MVP path is `integrations/upwork → services/ingestion → services/analytics`, exposed through CLI commands.

## Boundaries

Keep Upwork collection dumb and secret-safe:

- normalized job records only; no upstream private GraphQL envelopes in persisted raw records.
- diagnostics must redact credential/session/proxy/token material.
- no backend ranking, auto-apply, proposal/message generation, app-native scheduling, notifications, or UI in the core data engine.
- recommendation/ranking belongs in OpenClaw skills unless explicitly promoted later.
- no proxy acquisition docs or access-control bypass playbooks.

SQLite persistence belongs in ingestion/db/repository code. Analytics reads SQLite only. Scheduler/background execution is external/OpenClaw/OS responsibility and should call CLI commands.

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
