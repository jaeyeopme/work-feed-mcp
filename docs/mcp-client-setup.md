# MCP client setup

The Docker Compose runtime exposes the collector as a **Streamable HTTP MCP** endpoint, not a REST API.

Default endpoint:

```text
http://127.0.0.1:8000/mcp
```

If you override Compose env, derive the endpoint as:

```text
http://127.0.0.1:${WORK_FEED_MCP_PORT:-8000}${WORK_FEED_MCP_PATH:-/mcp}
```

## Start and check the runtime

```bash
make up
make status
```

Docker health checks prove container readiness and HTTP transport reachability for `/mcp`. They do **not** run a full MCP protocol initialize / tools/list / tool-call smoke. Run a protocol-level smoke from your MCP client if you need that evidence.

## Claude Code

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

## Codex

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

## What agents can do

Use the README MCP tools list as the source of truth for available tools. The MCP surface exposes collected job reads, run/status reads, and collector control queueing. It is not a REST API, not a recommendation engine, and not an auto-apply/proposal system.
