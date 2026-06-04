# Security Policy

## Supported versions

Security fixes target `main` and the latest tagged GitHub Release when one exists.

## Reporting a vulnerability

Use GitHub private vulnerability reporting when it is enabled. If it is
unavailable, open a minimal public issue asking for a private contact path.

Do not include exploit details, credentials, tokens, cookies, sessions, proxy
configuration, or live service data in public issues.

Safe context to include:

- affected version or commit;
- affected component, such as Docker runtime, MCP server, SQLite persistence,
  or Upwork normalization;
- expected impact;
- minimal reproduction steps that do not expose secrets or bypass access
  controls.

## Boundaries

This repository will not document or accept contributions for proxy acquisition,
access-control bypass, cookie/session setup, credential extraction, raw private
payload persistence, auto-apply, proposal/message automation, or backend ranking
engines.

Collection diagnostics must stay redacted and secret-safe.
