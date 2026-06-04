# ADR 0005: Keep Ranking Outside the Core Data Engine

## Status

Accepted

## Context

Collected jobs are meant to be consumed by agents. Backend scoring, Connects
guidance, proposal writing, and auto-apply workflows may look adjacent, but they
have different safety, UX, and business logic requirements from collection and
persistence.

Consuming agents may summarize already-collected jobs and apply user preferences
outside the data engine.

## Decision

The core project does not implement backend ranking, recommendation persistence,
proposal/message generation, or auto-apply behavior. Job selection and ranking
belong in the consuming agent layer unless a future project decision moves that
scope into the core data engine.

## Consequences

Positive:

- The backend stays simple and focused.
- MCP tools expose facts, not opaque recommendations.
- User-specific preferences stay outside durable core data.
- Risky application automation remains out of scope.

Tradeoffs:

- Agents must do their own candidate ranking.
- No central scoring history exists.
- Future recommendation features would require new contracts, tests, and safety
  rules before entering core scope.

## Alternatives Considered

- Add scores to ingested rows now: premature and likely to encode unstable user
  preferences.
- Build a backend recommendation service: useful later, but outside current
  Docker/MCP data-engine scope.
- Generate proposals from job rows: explicitly outside scope and higher risk.
