# AGENTS.md — upwork backend

## Role and intent

This repository is a conventional FastAPI backend for the Upwork job discovery pipeline. Keep responsibilities separated by app layer:

- `src/upwork_app/integrations/upwork`: Upwork/fixture collection, credential redaction, GraphQL transport, and normalized job records.
- `src/upwork_app/services`: application use cases for collection, ingestion, and analytics orchestration.
- `src/upwork_app/repositories` and `src/upwork_app/db`: SQLite persistence, schema, and query helpers.
- `src/upwork_app/api/routes`: HTTP request/response binding only.
- `src/upwork_app/schemas`: Pydantic request/response models.
- `src/upwork_app/cli`: local batch commands for the same use cases.

The implemented MVP path is `integrations/upwork → services/ingestion → services/analytics`, exposed through FastAPI and CLI.

## Boundaries

Keep Upwork collection dumb and secret-safe:

- normalized job records only; no upstream private GraphQL envelopes in persisted raw records.
- diagnostics must redact credential/session/proxy/token material.
- no ranking, auto-apply, proposal/message generation, scheduling, notifications, or UI in the MVP.
- no proxy acquisition docs or access-control bypass playbooks.

SQLite persistence belongs in ingestion/db/repository code. Analytics reads SQLite only. HTTP endpoints must not accept caller-selected local DB paths; web reads/writes use server-side settings such as `UPWORK_APP_DB`.

Use `docs/LLM_CONTEXT.md`, `docs/fastapi-backend-structure.md`, and `docs/contracts/job-jsonl.md` for detailed context.

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
