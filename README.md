# upwork

Docker/MCP-first local data engine for Upwork job discovery.

```text
Upwork visitor collection
  -> normalized records
  -> deduplicated SQLite storage
  -> MCP tools for lookup and collector control
  -> your agent handles UI, ranking, and decisions
```

This is not a REST web app, application bot, proposal generator, auto-apply tool, or built-in recommendation engine.

## Quick start

The normal user path is Docker Compose. It starts two services:

- `collector-worker`: runs the live collection loop and writes to SQLite.
- `upwork-collector-mcp`: exposes MCP tools over the same SQLite database.

```bash
cp .env.example .env
make up
make status
```

Configuration lives in `.env`. The defaults are conservative and work without credentials or cookies.

| Variable | Default | Meaning |
| --- | --- | --- |
| `UPWORK_COLLECTOR_LIVE` | `1` | Enable visitor-mode live collection in Docker. Set to `0` only for local debugging. |
| `UPWORK_COLLECTOR_INTERVAL_SECONDS` | `3600` | Wait time between worker collection runs. |
| `UPWORK_COLLECTOR_MAX_PAGES` | `5` | Maximum pages per run. |
| `UPWORK_COLLECTOR_PAGE_SIZE` | `50` | Jobs requested per page. |
| `UPWORK_COLLECTOR_QUERIES` | empty | Optional comma-separated searches such as `python,scraping`; empty means unfiltered/latest. |
| `UPWORK_COLLECTOR_LOG_LEVEL` | `INFO` | Worker log level. |
| `UPWORK_COLLECTOR_MCP_PORT` | `8000` | Host port for the local MCP endpoint. |
| `UPWORK_COLLECTOR_MCP_PATH` | `/mcp` | HTTP path for Streamable HTTP MCP. |

By default each run collects up to 250 jobs: `5 pages * 50 jobs`. After changing `.env`, restart the runtime:

```bash
make restart
```

## Connect an MCP client

Default endpoint:

```text
http://127.0.0.1:8000/mcp
```

If you override Compose env, derive it as:

```text
http://127.0.0.1:${UPWORK_COLLECTOR_MCP_PORT:-8000}${UPWORK_COLLECTOR_MCP_PATH:-/mcp}
```

See [MCP client setup](docs/mcp-client-setup.md) for a generic Streamable HTTP MCP client config.

## Operate the runtime

```bash
make status   # container status
make logs     # follow worker + MCP logs
make restart  # restart both services
make down     # stop the runtime
make config   # render docker compose config
```

## MCP tools

Job reads:

- `jobs_recent`
- `jobs_search`
- `jobs_get`

Run/status reads:

- `runs_recent`
- `collector_status`

Config/control queue:

- `config_get`
- `config_update`
- `collector_run_once`
- `collector_pause`
- `collector_resume`
- `collector_command_status`

Control tools are **enqueue-only**. They return immediately with a command id; the worker applies commands between collection runs.

```json
{ "ok": true, "command_id": "...", "status": "queued" }
```

Poll completion with `collector_command_status(command_id)`. Terminal states are `applied` and `failed`; in-flight states are `queued` and `running`.

`config_update` follows the same queue path and only accepts:

- `interval_seconds`
- `queries`
- `max_pages`
- `page_size`
- `paused`

`live` is intentionally not MCP-mutable.

Config precedence:

```text
1. worker startup seeds missing collector_config keys from Compose/.env
2. existing persisted keys are preserved across restarts
3. MCP config_update changes persisted keys through the command queue
4. Docker live mode remains an env/bootstrap setting
```

If MCP starts before the worker initializes SQLite, tools return stable `not_ready` payloads instead of creating schema from the read path:

```json
{ "ok": false, "error": "not_ready", "reason": "db_missing", "next_action": "start collector-worker" }
```

`reason` may be `db_missing` or `schema_missing`. An initialized DB with no rows is not an error; list tools return `{ "ok": true, "status": "empty", "rows": [] }`.

## What this does not do

- Not a REST API.
- Not a recommendation engine.
- Not auto-apply.
- Not proposal/message generation.
- Not notifications or report delivery.
- Not proxy/bypass tooling.
- Not cookie/session based collection guidance.

## Project structure

```text
src/upwork_app/integrations/upwork  Upwork visitor collection and normalization
src/upwork_app/services             collection, ingestion, analytics, health use cases
src/upwork_app/repositories         SQLite query/persistence helpers
src/upwork_app/db                   SQLite schema/connection helpers
src/upwork_app/domain               normalized collector contracts
src/upwork_app/runtime              collector worker runtime
src/upwork_app/mcp_server           agent-facing MCP tools
src/upwork_app/cli                  local/debug CLI entrypoints
```

Core flow:

```text
integrations/upwork
  -> services/scheduled_collection
  -> SQLite repositories/db
  -> services/analytics and MCP tools
```

## Developer reference

Development checks are maintained for contributors and local maintenance; they are not required for normal Docker/MCP usage.

```bash
make quality
make smoke
make e2e-smoke
make docker-compose-config
```

Direct Python CLI entrypoints exist for local debugging, but they are not the normal user interface. Prefer Docker/MCP for normal use.

```bash
uv run upwork-app --help
uv run upwork-app worker --help
uv run upwork-app mcp-server --help
```

Live collection evidence should be reported separately from local contract checks.

## Agent context

Use these docs as source of truth when giving this repo to another agent:

- `docs/LLM_CONTEXT.md`
- `docs/EXTERNAL_LLM_GUIDE.md`
- `docs/contracts/job-jsonl.md`

Boundary reminder for agents:

- Collection stays dumb and secret-safe.
- SQLite persistence belongs in repository/db/service code.
- Analytics and MCP read SQLite only.
- Recommendation/ranking belongs outside this data engine unless explicitly promoted later.
