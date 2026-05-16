# work-feed-mcp

Docker/MCP-first local data engine for collecting Upwork job listings into SQLite and exposing them to agents through MCP.

This project is not affiliated with, endorsed by, or sponsored by Upwork Inc. Upwork is referenced only as the source platform for collected public job listings.

License: MIT. See `CONTRIBUTING.md`, `SECURITY.md`, and `CHANGELOG.md` for maintainer notes.

```mermaid
sequenceDiagram
    participant U as Upwork job search
    participant W as work-feed-worker
    participant DB as SQLite volume
    participant M as work-feed-mcp
    participant A as Agent / MCP client

    W->>U: Collect public listings
    U-->>W: Job search responses
    W->>W: Normalize and deduplicate
    W->>DB: Store jobs and run summaries

    A->>M: jobs_recent / jobs_search / jobs_get
    M->>DB: Read collected jobs
    DB-->>M: Rows
    M-->>A: MCP tool result

    A->>M: config_update / collector_pause / collector_run_once
    M->>DB: Enqueue command
    W->>DB: Poll command queue
    W->>W: Apply between collection runs
```

This is not a REST web app, application bot, proposal generator, auto-apply tool, or built-in recommendation engine.

## Quick start

The normal user path is Docker Compose. It starts two services:

- `work-feed-worker`: runs the live collection loop and writes to SQLite.
- `work-feed-mcp`: exposes MCP tools over the same SQLite database.

```bash
cp .env.example .env
make up
make status
```

Configuration lives in `.env`. The defaults are conservative and work without credentials or cookies.

| Variable | Default | Meaning |
| --- | --- | --- |
| `WORK_FEED_LIVE` | `1` | Enable visitor-mode live collection in Docker. Set to `0` only for local debugging. |
| `WORK_FEED_DB` | `/data/work-feed.sqlite` | SQLite path inside the Docker volume. |
| `WORK_FEED_INTERVAL_SECONDS` | `3600` | Wait time between worker collection runs. |
| `WORK_FEED_MAX_PAGES` | `5` | Maximum pages per run. |
| `WORK_FEED_PAGE_SIZE` | `50` | Jobs requested per page. |
| `WORK_FEED_QUERIES` | empty | Optional comma-separated searches such as `python,scraping`; empty means unfiltered/latest. |
| `WORK_FEED_LOG_LEVEL` | `INFO` | Worker log level. |
| `WORK_FEED_MCP_HOST` | `0.0.0.0` | Container bind host for the MCP server. |
| `WORK_FEED_MCP_PORT` | `8000` | Host port for the local MCP endpoint. |
| `WORK_FEED_MCP_PATH` | `/mcp` | HTTP path for Streamable HTTP MCP. |

By default each run collects up to 250 jobs: `5 pages * 50 jobs`. After changing `.env`, recreate the runtime so Docker applies the new environment:

```bash
make restart
```

## Connect an MCP client

The Docker Compose runtime exposes a **Streamable HTTP MCP** endpoint, not a REST API.

Default endpoint:

```text
http://127.0.0.1:8000/mcp
```

If you override Compose env, derive it as:

```text
http://127.0.0.1:${WORK_FEED_MCP_PORT:-8000}${WORK_FEED_MCP_PATH:-/mcp}
```

Docker health checks prove container readiness and HTTP transport reachability for `/mcp`. They do **not** run a full MCP protocol initialize / tools/list / tool-call smoke. Run a protocol-level smoke from your MCP client if you need that evidence.

### Claude Code

Use Claude Code's HTTP MCP transport. Local scope is usually best for a personal Docker runtime because it stays private to your machine and current project.

```bash
claude mcp add --transport http work-feed http://127.0.0.1:8000/mcp
claude mcp list
```

Inside Claude Code, run:

```text
/mcp
```

If you want a project-scoped config instead, Claude Code can write a `.mcp.json` file:

```bash
claude mcp add --transport http --scope project work-feed http://127.0.0.1:8000/mcp
```

The equivalent JSON shape is:

```json
{
  "mcpServers": {
    "work-feed": {
      "type": "http",
      "url": "http://127.0.0.1:8000/mcp"
    }
  }
}
```

Claude Code also accepts `streamable-http` as a JSON alias for `http`, but the CLI examples above use `http` because that is the documented Claude Code command syntax.

### Codex

Use Codex's streamable HTTP MCP support. The CLI writes the shared Codex config used by the CLI and IDE extension.

```bash
codex mcp add work-feed --url http://127.0.0.1:8000/mcp
codex mcp list
```

The equivalent `~/.codex/config.toml` entry is:

```toml
[mcp_servers.work-feed]
url = "http://127.0.0.1:8000/mcp"
```

Codex infers streamable HTTP from `url`; do not add Claude-style `type` or `transport` fields to the TOML entry.

After connecting, ask your agent to call `jobs_recent` with `limit: 5` to confirm the MCP server responds. An empty result is okay on a fresh database. For a protocol-level check against a running MCP server, run:

```bash
make mcp-smoke
```

## Agent skill for collected jobs

This repository ships a project-local agent skill at `skills/work-feed-jobs`. Use it when an agent should read and summarize already-collected Upwork jobs through the work-feed MCP tools. Typical prompts include:

- `show recent collected jobs`
- `find python jobs`
- `pick recommendation candidates`
- `work-feed jobs`
- `Upwork collected jobs`

The skill also contains localized trigger examples for agent discovery. It is read-only over collected data. It prefers `jobs_recent`, `jobs_search`, `jobs_get`, `runs_recent`, and `collector_status`; it does not run live collection, configure schedules, operate Docker, write proposals/messages, auto-apply, or provide cookie/session/proxy/bypass guidance.

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

Live collection mode is set by Docker/.env at startup. MCP tools can pause/resume the worker and update schedule, query, and page settings, but they cannot switch the runtime between live and non-live modes.

Config precedence:

```text
1. worker startup seeds missing collector_config keys from Compose/.env
2. existing persisted keys are preserved across restarts
3. MCP config_update changes persisted keys through the command queue
4. Docker live mode remains an env/bootstrap setting
```

If MCP starts before the worker initializes SQLite, tools return stable `not_ready` payloads instead of creating schema from the read path:

```json
{ "ok": false, "error": "not_ready", "reason": "db_missing", "next_action": "start work-feed-worker" }
```

`reason` may be `db_missing`, `schema_missing`, or `unsupported_schema`. For `unsupported_schema`, upgrade work-feed or migrate the database before reading or controlling the runtime. An initialized DB with no rows is not an error; list tools return `{ "ok": true, "status": "empty", "rows": [] }`.

## What this does not do

- Not a REST API.
- Not a recommendation engine.
- Not auto-apply.
- Not proposal/message generation.
- Not notifications or report delivery.
- Not proxy/bypass tooling.
- Not cookie/session based collection guidance.

## Project structure

Runtime flow:

```text
Docker Compose
  work-feed-worker  -> recurring visitor collection -> SQLite volume
  work-feed-mcp     -> Streamable HTTP MCP tools -> agent client
```

Internal Python layout:

```text
src/work_feed_mcp/integrations/upwork  Upwork visitor collection and normalization
src/work_feed_mcp/services             collection, ingestion, analytics, health use cases
src/work_feed_mcp/repositories         SQLite query/persistence helpers
src/work_feed_mcp/db                   SQLite schema/connection helpers
src/work_feed_mcp/domain               normalized collector contracts
src/work_feed_mcp/runtime              collector worker runtime
src/work_feed_mcp/mcp_server           agent-facing MCP tools
src/work_feed_mcp/cli                  local/debug CLI entrypoints
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

Contributor and release references:

- `CONTRIBUTING.md` for setup, verification, scope boundaries, and PR expectations.
- `SECURITY.md` for vulnerability reporting and safe diagnostic rules.
- `CHANGELOG.md` for release notes.
- `docs/RELEASING.md` for GitHub Release and GHCR publishing steps.

```bash
make quality
make smoke
make e2e-smoke
make docker-compose-config
```

Direct Python CLI entrypoints exist for local debugging, but they are not the normal user interface. Prefer Docker/MCP for normal use.

```bash
uv run work-feed --help
uv run work-feed worker --help
uv run work-feed mcp-server --help
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
