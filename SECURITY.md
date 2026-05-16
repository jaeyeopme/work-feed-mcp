# Security Policy

## Supported versions

Until the project has a longer release history, security fixes target:

- the `main` branch;
- the latest tagged GitHub Release, when a release exists.

## Reporting a vulnerability

Use GitHub private vulnerability reporting for this repository when it is enabled. If that channel is unavailable, open a minimal public issue asking for a private contact path and do not include exploit details, credentials, tokens, cookies, sessions, proxy configuration, or live service data.

Please include only safe diagnostic context:

- affected version or commit;
- affected component, such as Docker runtime, MCP server, SQLite persistence, or Upwork normalization;
- expected impact;
- minimal reproduction steps that do not expose secrets or bypass access controls.

## Project security boundaries

This repository will not document or accept contributions that add:

- proxy acquisition or access-control bypass instructions;
- cookie/session setup guidance;
- credential extraction or token handling playbooks;
- persistence of upstream private payloads or raw snapshots;
- auto-apply, proposal/message automation, or backend ranking engines.

Collection diagnostics must stay redacted and secret-safe.
