# FastAPI backend structure

The project uses a single app-first structure because it is expected to behave like a common Python backend.

## Directory responsibilities

| Path | Responsibility |
| --- | --- |
| `src/upwork_app/main.py` | FastAPI application assembly |
| `src/upwork_app/api/routes` | HTTP-only routing and status-code mapping |
| `src/upwork_app/schemas` | Pydantic request/response models |
| `src/upwork_app/services` | Use-case orchestration such as collect, ingest, analytics |
| `src/upwork_app/repositories` | SQLite-oriented persistence/query helpers |
| `src/upwork_app/db` | SQLite connection and schema setup |
| `src/upwork_app/domain` | Domain validation and internal data types |
| `src/upwork_app/integrations/upwork` | Upwork-specific transport, GraphQL, credentials, normalization |
| `src/upwork_app/cli` | Local batch commands that call the same services as the API |
| `tests` | App-level API/service tests and fixtures |

## API shape

- `GET /health`
- `POST /collect`
- `POST /ingest` — accepts either `jobs: [...]` or `jsonl`, exactly one
- `POST /collect-and-ingest` — MVP convenience endpoint returning insert/skip counts and new jobs
- `POST /runs/collect` — run-style collect+ingest endpoint returning insert/skip counts and new jobs
- `GET /analytics/{summary|skills|jobs|budgets|clients}`

HTTP endpoints use the server-side `UPWORK_APP_DB` setting for SQLite access. Caller-chosen database paths are CLI-only to avoid exposing arbitrary filesystem reads/writes through the web API.

Persistence is intentionally jobs-only: new SQLite databases contain `jobs` and `job_skills`. The app does not persist run history, raw record archives, or observation logs.

## Local command runner

The repository uses `make` for short local commands:

```bash
make dev
make run
make quality
make smoke
make e2e-smoke
```

## Safety

Live collection keeps the `UPWORK_COLLECTOR_LIVE=1` gate and credential redaction behavior. Tests and smoke checks use fixtures only.

Analytics routes are intentionally explicit instead of a dynamic `/{name}` dispatcher so OpenAPI docs and future query-specific parameters stay clear.
