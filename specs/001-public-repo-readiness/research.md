# Research: Public Repository Readiness

## Decision: README is the normal-user source of truth

**Rationale**: The target user should be able to clone, configure, start, operate, connect an MCP client, understand counters, and troubleshoot common states from one document. Splitting normal usage across several docs increases the chance that public users follow stale or maintainer-specific instructions.

**Alternatives considered**:

- Separate `SELF_HOSTING.md`, `CONFIGURATION.md`, and `TROUBLESHOOTING.md`: rejected for this feature because the user explicitly prefers avoiding unnecessary docs and keeping README sufficient.
- Keep README short and link out: rejected because the key pain point is that public users should not need to search multiple documents.

## Decision: Standard Docker Compose is the canonical quick start

**Rationale**: Docker Compose is the portable runtime interface visible in the repository. Make can remain useful for maintainers and frequent users, but public quick start should work in environments where Make is unavailable.

**Alternatives considered**:

- Keep `make up` as the main quick start: rejected because it adds an avoidable tool prerequisite for first-time users.
- Replace Make entirely: rejected because existing wrappers remain useful as convenience commands and verification entrypoints.

## Decision: Private Oracle deployment artifacts are deleted or rewritten out of the public surface

**Rationale**: Personal server deployment workflows, scripts, docs, tests that require them, `ORACLE_*` secrets, SSH setup, host paths, and rollback runbooks make the repository look tailored to one maintainer's infrastructure and create avoidable safety and trust concerns for public users.

**Alternatives considered**:

- Keep deployment but document it as maintainer-only: rejected because active public workflows and scripts still expose private deployment policy and secret names.
- Move deployment into a generic self-hosting guide: rejected for this feature because the README should cover normal local operation and private server deployment is not needed for public use.
- Keep tests that require private deploy files: rejected because they would force deleted private deployment artifacts back into the public repository.

## Decision: CI remains verification-only

**Rationale**: Public CI should demonstrate repository health without requiring private credentials or mutating an external server. Verification-only CI is easier for contributors to understand and safer for forks.

**Alternatives considered**:

- Keep deployment gated after quality checks: rejected because it still requires private server secrets and confuses public automation intent.
- Use path filters to decide deployment relevance: rejected because there is no public deployment job after this cleanup.

## Decision: Release automation remains as public artifact publishing only

**Rationale**: A GHCR image or GitHub Release can help users consume the project later, but release automation must not be coupled to a maintainer's private runtime.

**Alternatives considered**:

- Remove all release automation now: acceptable but not required by the spec; keeping public artifact release is compatible with the target boundary.
- Treat release as deployment: rejected because public artifact publishing and private server deployment are different user-visible behaviors.

## Decision: Planning artifacts are synchronized after clarification

**Rationale**: Clarification ran after the initial plan, so plan, research, data-model, contract, and quickstart artifacts need to match the clarified decisions before task generation. Otherwise task generation could preserve stale private deployment expectations.

**Alternatives considered**:

- Update only the spec: rejected because downstream tasks consume the plan artifacts too.
- Delete plan artifacts and rerun planning: rejected because the existing artifacts are small and can be updated directly without changing the decisions.

## Decision: Run counter and dedupe definitions belong in README

**Rationale**: `seen`, `inserted`, `skipped`, and `job_id` deduplication affect normal interpretation of collector status. They are not only data-model details; users see them during operation.

**Alternatives considered**:

- Put definitions only in a data model doc: rejected because normal users should not need docs beyond README.
- Rename counters: rejected because it would change existing behavior and contracts outside this feature's scope.

## Decision: Worker blocked-state resilience is excluded

**Rationale**: Upstream blocked handling changes runtime failure semantics, health behavior, retry/backoff, and status taxonomy. That deserves a separate architecture discussion and feature spec after public repository cleanup.

**Alternatives considered**:

- Include blocked resilience now: rejected because it broadens the feature from public surface cleanup into runtime behavior.
- Hide blocked behavior in docs: rejected because documentation should accurately state the current operational condition and mark resilience as future work.
