# ADR 0004: Persist Normalized Records, Not Raw Upstream Payloads

## Status

Accepted

## Context

Source collection receives upstream response shapes that may include fields not
appropriate for durable storage or agent-facing output. Persisting raw envelopes
would simplify debugging, but it increases privacy, security, and
platform-boundary risk.

The repository already defines a normalized job JSONL contract and rejects
private/access-material fields in collector records.

## Decision

The system persists normalized public job records, job skills, and redacted
operational run summaries. It does not persist upstream private GraphQL
envelopes, raw snapshots, cookies, sessions, tokens, proxies, or per-job
observation logs.

Downstream code consumes the normalized collector contract, not source transport
internals.

## Consequences

Positive:

- Durable state is safer to inspect.
- Agent-facing outputs stay scoped and predictable.
- Integration-specific response shapes remain behind the integration boundary.

Tradeoffs:

- Debugging upstream schema drift may require fresh fixture capture or
  sanitized examples.
- The database cannot answer historical change/observation questions.
- Adding richer fields requires explicit contract and schema updates.

## Alternatives Considered

- Store full raw responses: higher debugging value, but not aligned with the
  project's safety boundary.
- Store raw normalized JSON blobs per job: useful for replay, but currently out
  of scope and not needed by MCP tools.
- Store per-job observation history: useful for analytics, but explicitly out of
  current scope.
