# Architecture Decision Records

This directory records the core architecture decisions currently implemented in
`work-feed-mcp`. The first ADR set is reconstructed from existing documentation,
tests, and source behavior.

ADR status values:

- `Accepted`: current implementation follows the decision.
- `Superseded`: decision was replaced by a later ADR.
- `Proposed`: decision is not yet implemented.

Current ADRs:

- [0001 - Docker/MCP-first runtime](0001-docker-mcp-first-runtime.md)
- [0002 - Worker-owned SQLite schema](0002-worker-owned-sqlite-schema.md)
- [0003 - MCP control tools enqueue commands](0003-mcp-control-tools-enqueue-commands.md)
- [0004 - Persist normalized records, not raw upstream payloads](0004-persist-normalized-records-not-raw-upstream-payloads.md)
- [0005 - Keep ranking outside the core data engine](0005-keep-ranking-outside-core-data-engine.md)
