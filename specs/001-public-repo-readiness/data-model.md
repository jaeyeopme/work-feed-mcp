# Data Model: Public Repository Readiness

This feature changes public-facing repository surfaces, not runtime persistence. Entities below describe documentation and automation contracts to preserve during implementation.

## Public README

**Purpose**: Primary normal-user document.

**Required fields/sections**:

- Project purpose and non-goals.
- Safety boundary for Upwork-related collection.
- Standard Docker Compose quick start.
- Configuration summary tied to `.env.example`.
- MCP client connection instructions.
- Runtime operation commands.
- Run counter and `job_id` deduplication definitions.
- Troubleshooting for common startup, database, MCP, config, and upstream states.
- Make commands listed only as convenience wrappers.

**Validation rules**:

- Must be sufficient for normal startup and operation without requiring `docs/`.
- Must not present `make up` as the canonical quick start.
- Must not contain private deployment instructions or private server rollback steps.

## Example Environment

**Purpose**: Copyable local runtime configuration.

**Required fields/sections**:

- Live mode, database path, collection cadence, query limits, query filters, log level, and MCP host/port/path.
- Comments that align with README quick start.

**Validation rules**:

- Must not make Make a prerequisite.
- Must not include credentials, cookies, sessions, proxies, private hosts, or cloud-specific values.

## Public Automation Surface

**Purpose**: Repository workflows and scripts visible to contributors and users.

**Required states**:

- CI verification runs quality, coverage, smoke, and e2e smoke checks.
- Release automation publishes GHCR/GitHub Release public artifacts only.
- No active private deployment workflow or script remains.

**Validation rules**:

- Normal CI must not require SSH credentials or private server paths.
- Active workflows and scripts must not contain `ORACLE_*` secrets, Oracle deploy jobs, private SSH deploy steps, `/home/ubuntu` paths, or private rollback runbooks.
- Tests must not require private deployment workflows, scripts, or docs to exist.

## Run Summary Counters

**Purpose**: User-facing interpretation of collector status and run history.

**Fields**:

- `seen`: number of rows observed or fetched during a run.
- `inserted`: number of newly stored unique jobs.
- `skipped`: number of observed rows not stored because an existing job already had the same identity.

**Validation rules**:

- README must define all three counters.
- Definitions must make clear that skipped duplicates are not collector failures.

## Job Identity

**Purpose**: User-facing deduplication key.

**Fields**:

- `job_id`: stable job identity used to deduplicate stored jobs.

**Validation rules**:

- README must state that stored jobs are deduplicated by `job_id`.
- This feature must not change the stored key or historical deduplication behavior.

## Private Deployment Artifact

**Purpose**: Maintainer-specific deployment material that must not remain active in public repository surfaces.

**Examples**:

- Oracle Cloud deployment docs.
- `ORACLE_*` secret names.
- SSH deployment workflows.
- `/home/ubuntu` or other personal server paths.
- Personal server rollback/runbook scripts.
- Contract tests that require private deployment artifacts to exist.

**Validation rules**:

- Must be removed from active public workflows, scripts, normal-user docs, and tests that require them.
- If any private operational knowledge is retained outside the public path, it must not be required or referenced by README usage.
