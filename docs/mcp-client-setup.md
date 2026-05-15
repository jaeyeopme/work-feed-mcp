# MCP client setup

The Docker Compose runtime exposes the collector as a **Streamable HTTP MCP** endpoint, not a REST API.

Default endpoint:

```text
http://127.0.0.1:8000/mcp
```

If you override Compose env, derive the endpoint as:

```text
http://127.0.0.1:${UPWORK_COLLECTOR_MCP_PORT:-8000}${UPWORK_COLLECTOR_MCP_PATH:-/mcp}
```

## Start and check the runtime

```bash
make up
make status
```

Docker health checks prove container readiness and HTTP transport reachability for `/mcp`. They do **not** run a full MCP protocol initialize / tools/list / tool-call smoke. Run a protocol-level smoke from your MCP client if you need that evidence.

## Generic client config shape

Exact config syntax varies by MCP client and version. Use the client's Streamable HTTP MCP server configuration and point it at the endpoint above.

Generic shape:

```json
{
  "mcpServers": {
    "upwork-collector": {
      "transport": "streamable-http",
      "url": "http://127.0.0.1:8000/mcp"
    }
  }
}
```

If your client uses a different field name, keep the same semantic values: server name `upwork-collector`, Streamable HTTP transport, and URL `http://127.0.0.1:8000/mcp`.

## What agents can do

Use the README MCP tools list as the source of truth for available tools. The MCP surface exposes collected job reads, run/status reads, and collector control queueing. It is not a REST API, not a recommendation engine, and not an auto-apply/proposal system.
