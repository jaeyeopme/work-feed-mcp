# Feature Specification: Public Repository Readiness

**Feature Branch**: `[001-public-repo-readiness]`

**Created**: 2026-05-30

**Status**: Draft

**Input**: User description: "Make the public repository understandable, runnable, and safe for another person to clone, run, and operate. The README should be the primary user document, the quick start should use standard Docker Compose, personal Oracle Cloud deployment traces should be removed or separated, CI should run verification only, run-result counters and job deduplication should be documented, and Upwork-related safety boundaries should be explicit."

## Clarifications

### Session 2026-05-30

- Q: Which documentation should remain outside README? → A: README contains all normal-user usage; developer docs may remain as optional references and must not be required for normal use.
- Q: Should the release workflow remain? → A: Keep the GHCR/GitHub Release workflow as public artifact publishing, with no private server deployment.
- Q: How should private deployment artifacts be handled? → A: Delete Oracle/private deploy scripts, docs, workflows, and tests that require them from the public repository surface.
- Q: How should post-plan clarification changes be handled? → A: Sync the spec changes into plan, research, data-model, contracts, and quickstart before task generation.

## User Scenarios & Testing *(mandatory)*

### User Story 1 - Start and Operate From the README (Priority: P1)

A new local operator can clone the repository, copy the example environment, start the runtime, inspect status, view logs, restart, stop, and connect an MCP client by reading only the README.

**Why this priority**: The public repository succeeds only if a new user can run and operate the project without knowing the maintainer's private setup or searching through multiple documents.

**Independent Test**: Give the README to a user with Docker Compose and an MCP client available. The user can complete the documented startup and basic operation flow without opening any other project document.

**Acceptance Scenarios**:

1. **Given** a fresh checkout, **When** the user follows the README quick start, **Then** the documented commands start the worker and MCP services and show their status.
2. **Given** a running runtime, **When** the user follows the README operation commands, **Then** they can inspect status, follow logs, restart, and stop the runtime.
3. **Given** a running MCP endpoint, **When** the user follows the README client setup, **Then** they can connect an MCP client and perform a basic job/status tool check.

---

### User Story 2 - Trust the Public Automation Surface (Priority: P2)

A public reader can inspect repository automation and see verification workflows, optional public release artifacts, and no personal server deployment path, private cloud secrets, or maintainer-specific rollback runbook.

**Why this priority**: Public automation is a trust surface. Private deployment logic in a public repo creates confusion and suggests the project is tailored to one maintainer's server rather than general local use.

**Independent Test**: Inspect the active workflows, scripts, and user-facing documentation. They describe verification and optional public releases only, with no active private server deployment, cloud-specific secret names, or personal host paths.

**Acceptance Scenarios**:

1. **Given** the repository automation files, **When** a reader searches for private deployment terms, **Then** no active workflow or script performs personal server deployment.
2. **Given** a pull request or push, **When** CI runs, **Then** it performs verification checks only and does not require SSH credentials, private cloud secrets, or server paths.
3. **Given** release automation is retained, **When** a release runs, **Then** it creates public distributable artifacts only and does not deploy to a private host.

---

### User Story 3 - Understand Data Counts and Safety Boundaries (Priority: P3)

A user can understand what collection run counts mean, how duplicate jobs are handled, and what the project intentionally does not provide.

**Why this priority**: Run summaries and Upwork-related boundaries are frequent sources of confusion. Clear definitions prevent misinterpreting duplicates as data loss and make safe use expectations explicit.

**Independent Test**: Read the README and verify it defines run counters, job deduplication, and safety limits without requiring a data model document.

**Acceptance Scenarios**:

1. **Given** a run summary with `seen`, `inserted`, and `skipped`, **When** the user reads the README, **Then** they can explain that `seen` is observed rows, `inserted` is newly saved unique jobs, and `skipped` is already-stored duplicates.
2. **Given** the jobs table behavior, **When** the user reads the README, **Then** they understand jobs are deduplicated by `job_id`.
3. **Given** the project handles Upwork job listing data, **When** the user reads the README, **Then** they see the non-affiliation, authorized-data, no credential guidance, no raw private payload, no proposal generation, and no auto-apply boundaries.

### Edge Cases

- A user without `make` installed can still follow the canonical quick start and operation commands.
- Users who prefer Make can still discover Make commands as optional wrappers, not as the main path.
- A fresh database with no collected jobs is documented as a valid empty state, not a failure.
- A not-ready database, unavailable worker, or MCP connection failure has a visible troubleshooting path in the README.
- A blocked or unavailable upstream source is documented as an operational condition, while worker resilience changes remain outside this feature's scope.
- Existing developer or architecture documents that remain must not contradict the README, must not reintroduce personal deployment as the public workflow, and must not be required for normal usage.
- The public release workflow must not be confused with deployment to a maintainer's private server.
- Tests that currently require private deployment workflows, scripts, or docs must be removed or rewritten to assert the public repository boundary instead.

## Requirements *(mandatory)*

### Functional Requirements

- **FR-001**: The README MUST be sufficient for a normal local Docker/MCP user to understand the project, start it, operate it, connect an MCP client, and understand common failure states without reading any other project document.
- **FR-002**: The README quick start MUST present standard Docker Compose commands as the canonical startup path, including clone, entering the repository, copying `.env.example`, starting with build, and checking service status.
- **FR-003**: Make commands MAY remain documented, but they MUST be presented as convenience wrappers rather than the primary user path.
- **FR-004**: The example environment file MUST align with the README quick start and MUST not make Make a prerequisite for normal use.
- **FR-005**: The README MUST include common operation commands for viewing logs, restarting, stopping, inspecting status, and checking the collector/MCP runtime.
- **FR-006**: The README MUST explain how to connect at least one MCP client and how to confirm the MCP server responds, including the empty-database success case.
- **FR-007**: The README MUST define `seen`, `inserted`, `skipped`, and `job_id` deduplication in user-facing language.
- **FR-008**: The README MUST state the safety boundaries: no Upwork affiliation, collect only authorized data, no cookie/session/proxy bypass guidance, no raw private payload persistence, no proposal/message generation, and no auto-apply.
- **FR-009**: The README MUST include troubleshooting guidance for an empty database, database not ready, MCP connection failure, configuration changes not taking effect until runtime recreation or restart, and blocked or unavailable upstream collection.
- **FR-010**: Active public workflows MUST run verification only for normal CI and MUST NOT deploy to a private host or require private server secrets.
- **FR-011**: The release workflow SHOULD remain as GHCR/GitHub Release public artifact publishing and MUST NOT deploy to a private server.
- **FR-012**: Oracle/private deployment scripts, docs, workflows, and tests that require them MUST be deleted or rewritten so the public repository surface contains no personal Oracle Cloud deployment logic, `ORACLE_*` secret names, `/home/ubuntu` paths, private SSH deployment steps, or personal rollback runbooks.
- **FR-013**: Remaining developer or maintainer docs MAY exist as optional deep references, but normal user startup, operation, counter definitions, and troubleshooting MUST remain in the README and MUST NOT require users to read those docs.
- **FR-014**: Verification contracts MUST reflect the public repository scope and fail if private deployment traces return to active public docs, workflows, or scripts.
- **FR-015**: This feature MUST NOT change collection behavior, persistence schema, MCP tool semantics, or worker blocked-state resilience.

### Key Entities

- **Public README**: Primary user-facing document for project purpose, safety boundaries, quick start, operation, MCP connection, counter definitions, and troubleshooting.
- **Example Environment**: Copyable configuration starting point whose comments and defaults match the README path.
- **Runtime Operation Commands**: User-visible commands for status, logs, restart, shutdown, configuration inspection, and collector/MCP checks.
- **Run Summary Counters**: `seen`, `inserted`, and `skipped` values shown in run history and collector status.
- **Job Identity**: `job_id` as the deduplication key users rely on when interpreting inserted versus skipped jobs.
- **Public Automation Surface**: CI and release workflows visible to public contributors and users.
- **Private Deployment Artifacts**: Personal cloud deployment workflows, scripts, docs, tests, secrets, paths, and rollback procedures that must not remain part of the public repository surface.
- **Affected Layers**: Public documentation, example configuration, workflow automation, helper command documentation, documentation contract tests.
- **Data Contracts**: Run summary counter meanings and `job_id` deduplication documentation only; no schema, collector payload, or MCP response shape changes are in scope.

## Success Criteria *(mandatory)*

### Measurable Outcomes

- **SC-001**: A first-time local user can complete the README startup and status check in under 10 minutes without opening another project document.
- **SC-002**: The normal-user portion of the README includes 100% of the required startup, operation, MCP connection, counter-definition, and troubleshooting topics listed in this specification.
- **SC-003**: Searches of active public docs, workflows, and scripts find zero private Oracle deployment references, `ORACLE_*` secret names, personal host paths, private SSH deployment steps, or personal rollback runbooks.
- **SC-004**: Normal CI contains verification jobs only and references zero private server deployment secrets or SSH deployment steps.
- **SC-005**: The README defines all four data interpretation terms: `seen`, `inserted`, `skipped`, and `job_id` deduplication.
- **SC-006**: Documentation and workflow contract tests that cover public-readiness requirements pass, or any skipped verification is listed with reason and residual risk.
- **SC-007**: Existing Docker/MCP runtime behavior remains compatible with current users: worker and MCP services, local MCP endpoint, and existing read/control tool expectations are not intentionally changed.
- **SC-008**: The release workflow publishes public artifacts only and contains zero private server deployment steps.

## Assumptions

- The feature description is taken from the current conversation about public repository readiness and the immediately preceding repository status review.
- The target user persona is a local Docker Compose user with an MCP client, not a maintainer operating a private server.
- README-first means normal users should not need `docs/` to start, operate, or troubleshoot the project.
- Optional developer or maintainer documents may remain if they do not contradict the README and are not required for normal use.
- Public release automation remains in scope as GHCR/GitHub Release artifact publishing only.
- Worker behavior when upstream collection is blocked is a follow-up implementation concern and is intentionally out of scope for this specification.
- Clarification ran after planning, so planning artifacts must be synchronized with the clarified spec before task generation.
