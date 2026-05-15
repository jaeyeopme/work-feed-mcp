# upwork

Upwork job discovery를 위한 **Docker/MCP-first local data engine**입니다.

역할은 단순합니다.

```text
Upwork visitor collection
  -> normalized records
  -> SQLite에 중복 없이 저장
  -> MCP tools로 조회/제어
  -> agent가 UI/추천/의사결정 담당
```

이 저장소는 REST 웹 애플리케이션이 아닙니다. 자동 지원, proposal/message 생성, auto-apply, 내장 recommendation engine은 범위 밖입니다.

## User guide

### Start the runtime

Docker Compose가 기본 사용 경로입니다. Compose를 시작하면 collector worker가 live collection loop를 실행하고, MCP service가 같은 SQLite DB를 읽고 제어 명령을 큐에 넣습니다.

```bash
docker compose up -d
```

Readiness는 Docker/Compose 기준으로 확인합니다.

```bash
docker compose ps
docker compose logs -f collector-worker
docker compose logs -f upwork-collector-mcp
```

Docker runtime live mode is the normal user path. 일반 사용자 관점에서 live가 정상 경로입니다. 기본값은 보수적으로 설정되어 있습니다.

- interval: 60 minutes
- max pages: 5
- page size: 50
- query: unfiltered/latest

필요하면 `.env` 또는 Compose environment variables로 조정합니다.

```bash
cp .env.example .env
# edit UPWORK_COLLECTOR_INTERVAL_SECONDS, UPWORK_COLLECTOR_QUERIES, etc.
docker compose up -d
```

### Connect an MCP client

MCP endpoint:

```text
http://127.0.0.1:8000/mcp
```

If you override Compose env, derive it as:

```text
http://127.0.0.1:${UPWORK_COLLECTOR_MCP_PORT:-8000}${UPWORK_COLLECTOR_MCP_PATH:-/mcp}
```

See [MCP client setup](docs/mcp-client-setup.md) for the generic Streamable HTTP MCP client shape.

### MCP tools

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

### MCP v1 control contract

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

### What this does not do

- Not a REST API.
- Not a recommendation engine.
- Not auto-apply.
- Not proposal/message generation.
- Not notifications or report delivery.
- Not proxy/bypass tooling.
- Not cookie/session based collection guidance.

## CLI reference

The Docker/MCP path above is the primary user interface. These CLI commands remain available for local operation, compatibility, and agents that need direct JSON outputs.

### `upwork-app`

Top-level command dispatcher:

```bash
uv run upwork-app --help
uv run upwork-app health --help
uv run upwork-app worker --help
uv run upwork-app mcp-server --help
```

Useful subcommands:

- `upwork-app worker` — run the collector worker loop.
- `upwork-app mcp-server` — run the MCP server.
- `upwork-app health` — check runtime readiness.
- `upwork-app collect-scheduled` — run one scheduled collection pass.
- `upwork-app scheduler-status` — print recent collection status.
- `upwork-app scheduler ...` — wrap native scheduler control commands.

### Analytics CLIs

These commands read SQLite and print JSON for agents or scripts:

```bash
uv run upwork-app-analytics summary --db ./data/upwork.sqlite
uv run upwork-app-analytics skills --db ./data/upwork.sqlite
uv run upwork-app-analytics jobs --db ./data/upwork.sqlite
uv run upwork-app-analytics budgets --db ./data/upwork.sqlite
uv run upwork-app-analytics clients --db ./data/upwork.sqlite
```

### Collection CLIs

One-shot collection and ingestion CLIs remain available for advanced/native workflows:

```bash
uv run upwork-app-collect --help
uv run upwork-app-ingest --help
uv run upwork-app collect-scheduled --help
```

`upwork-app-ingest` output includes `new_jobs`, which an external agent can consume as recommendation candidates. This project does not score or rank them internally.

## Native/server notes

Docker Compose + MCP is the public default. Native scheduler and server installation notes are retained for personal/legacy deployments:

- `docs/scheduler-plan.md`
- `docs/server-install.md`

Native scheduler commands are wrappers around host scheduler tools, so use them only when you intentionally run the project outside Docker Compose.

## Project structure

```text
src/upwork_app/integrations/upwork  Upwork visitor collection and normalization
src/upwork_app/services             collection, ingestion, analytics, health use cases
src/upwork_app/repositories         SQLite query/persistence helpers
src/upwork_app/db                   SQLite schema/connection helpers
src/upwork_app/domain               normalized collector contracts
src/upwork_app/cli                  stable local CLI entrypoints
src/upwork_app/mcp_server           agent-facing MCP tools
```

Core flow:

```text
integrations/upwork
  -> services/ingestion
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

Live collection evidence should be reported separately from local contract checks.

## LLM/agent quick context

Use these docs as source of truth when giving this repo to another agent:

- `docs/LLM_CONTEXT.md`
- `docs/EXTERNAL_LLM_GUIDE.md`
- `docs/contracts/job-jsonl.md`

Boundary reminder for agents:

- Collection stays dumb and secret-safe.
- SQLite persistence belongs in repository/db/service code.
- Analytics and MCP read SQLite only.
- Recommendation/ranking belongs outside this data engine unless explicitly promoted later.
