# FastAPI backend structure

The project uses an app-first structure because it is now expected to behave like a common Python backend.

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

## Migration rule

Add new backend behavior under `src/upwork_app`. Keep the old `packages/*` modules stable until all callers have migrated, then remove them in a separate cleanup pass.

## API shape

- `GET /health`
- `POST /collect`
- `POST /ingest`
- `POST /collect-and-ingest`
- `GET /analytics/{summary|skills|jobs|budgets|runs|clients}`

## Safety

Live collection keeps the existing `UPWORK_COLLECTOR_LIVE=1` gate and credential redaction behavior. Tests and smoke checks use fixtures only.

HTTP endpoints use the server-side `UPWORK_APP_DB` setting for SQLite access. Caller-chosen database paths are CLI-only to avoid exposing arbitrary filesystem reads/writes through the web API.

## Local command runner

The repository includes a `justfile` for short local commands:

```bash
just dev
just quality
just smoke
just e2e
just dupe
```

`make` remains as the compatibility verification surface used by existing docs and legacy package checks.
