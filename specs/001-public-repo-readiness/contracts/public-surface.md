# Contract: Public Repository Surface

This contract defines the observable public repository state after implementation. It is intentionally written as checks a reviewer or contract test can apply.

## README Contract

- The quick start uses standard Docker Compose commands:
  - copy `.env.example` to `.env`
  - start with build
  - inspect service status
- `make up` and related Make commands may appear only as convenience wrappers.
- README contains all normal-user startup, operation, MCP connection, counter definition, and troubleshooting guidance.
- Developer docs may remain as optional references, but README must not require them for normal usage.
- The normal-user portion of README includes:
  - project purpose and non-goals
  - Upwork non-affiliation and authorized-data boundary
  - no cookie/session/proxy/bypass guidance
  - no raw private payload persistence
  - no proposal/message generation
  - no auto-apply
  - MCP endpoint and at least one client connection path
  - empty database success behavior
  - database not-ready behavior
  - operation commands for status, logs, restart, shutdown, and runtime checks
  - definitions for `seen`, `inserted`, `skipped`, and `job_id` deduplication

## Environment Contract

- `.env.example` comments match the Docker Compose quick start.
- `.env.example` does not require Make.
- `.env.example` does not contain private hostnames, credentials, cookies, sessions, proxies, or cloud-specific deployment variables.

## CI Contract

- The normal CI workflow runs verification only.
- The normal CI workflow does not define private deployment jobs.
- The normal CI workflow does not require SSH credentials, `ORACLE_*` secrets, private host paths, or known-host entries.
- Verification includes the repository's quality, coverage, smoke, and e2e smoke commands unless an implementation explicitly narrows that with documented reason.

## Release Contract

- The release workflow remains scoped to GHCR/GitHub Release public artifact publishing.
- The release workflow must not start a runtime on a private host.
- The release workflow must not contain SSH deployment steps or private cloud secret names.

## Private Deployment Removal Contract

Active public docs, scripts, and workflows must not contain:

- Oracle Cloud deployment instructions
- `ORACLE_*` secret names
- private SSH deployment setup
- `/home/ubuntu` paths
- personal server rollback/runbook steps
- active deployment relevance scripts for a maintainer server

Tests must not require those private deployment docs, scripts, or workflows to exist.

## Out-of-Scope Contract

Implementation must not change:

- collection behavior
- persisted schema
- MCP tool names or payload semantics
- worker health semantics
- blocked/upstream retry behavior
