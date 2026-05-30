# Tasks: Public Repository Readiness

**Input**: Design documents from `specs/001-public-repo-readiness/`

**Prerequisites**: `plan.md`, `spec.md`, `research.md`, `data-model.md`, `contracts/public-surface.md`, `quickstart.md`

**Tests**: Included because the spec requires public-readiness verification contracts and zero regression in Docker/MCP runtime expectations. Live upstream tests are out of scope.

**Organization**: Tasks are grouped by user story to enable independent implementation and testing.

## Format: `[ID] [P?] [Story] Description`

- **[P]**: Can run in parallel because it touches different files or only reads files
- **[Story]**: User story label, present only in user story phases
- Every task names the exact repository path(s) it touches or verifies

## Phase 1: Setup (Shared Inventory)

**Purpose**: Establish the current public surface before changing tests or docs.

- [X] T001 [P] Run the private-deployment inventory command from `specs/001-public-repo-readiness/quickstart.md` against `README.md`, `.github/`, `scripts/`, and `docs/`
- [X] T002 [P] Compare the current README and environment comments against `specs/001-public-repo-readiness/contracts/public-surface.md`, `README.md`, and `.env.example`
- [X] T003 [P] Identify obsolete Oracle/private deploy tests in `tests/docker/test_deploy_workflow_contract.py`, `tests/docker/test_oracle_deploy_decision.py`, `tests/docker/test_oracle_deploy_script_contract.py`, and `tests/docker/test_oracle_deploy_script_behavior.py`

---

## Phase 2: Foundational (Contract Test Direction)

**Purpose**: Make tests describe the clarified public repository contract before implementation.

**Critical**: Complete this phase before user-story implementation so failing tests describe the target state.

- [X] T004 Update normal-user README assertions in `tests/docker/test_docs_contract.py` to remove old `make up` primary-path expectations and any requirement to read `docs/`
- [X] T005 [P] Update public OSS readiness policy assertions in `tests/docker/test_oss_readiness_contract.py` to allow developer docs as optional references
- [X] T006 [P] Update release workflow policy assertions in `tests/docker/test_release_workflow_contract.py` to forbid private SSH/server deployment steps
- [X] T007 Delete or rewrite private deployment contract tests in `tests/docker/test_deploy_workflow_contract.py`, `tests/docker/test_oracle_deploy_decision.py`, `tests/docker/test_oracle_deploy_script_contract.py`, and `tests/docker/test_oracle_deploy_script_behavior.py`

**Checkpoint**: `tests/docker` should now encode the desired public surface and fail until implementation catches up.

---

## Phase 3: User Story 1 - Start and Operate From the README (Priority: P1) MVP

**Goal**: A first-time local operator can start, inspect, operate, and connect the runtime by reading only `README.md`.

**Independent Test**: `tests/docker/test_docs_contract.py` passes for the normal-user README contract, and a reader can follow the README quick start without `make`.

### Tests for User Story 1

- [X] T008 [P] [US1] Add README quick-start assertions in `tests/docker/test_docs_contract.py` for `cp .env.example .env`, `docker compose up -d --build`, and `docker compose ps`
- [X] T009 [P] [US1] Add environment-comment assertions in `tests/docker/test_docs_contract.py` for `.env.example` not requiring `make`
- [X] T010 [P] [US1] Add operation-command assertions in `tests/docker/test_docs_contract.py` for `docker compose logs -f`, `docker compose restart`, `docker compose down`, and `docker compose exec work-feed-worker work-feed scheduler-status --db /data/work-feed.sqlite`

### Implementation for User Story 1

- [X] T011 [US1] Rewrite the `README.md` quick start to use clone, `cd work-feed-mcp`, `cp .env.example .env`, `docker compose up -d --build`, and `docker compose ps`
- [X] T012 [US1] Update the `README.md` operation section to show Docker Compose status, logs, restart, shutdown, config inspection, scheduler status, and MCP smoke commands
- [X] T013 [US1] Move Make commands in `README.md` into a convenience-wrapper section that does not present `make up` as the primary path
- [X] T014 [US1] Update `.env.example` comments to match the Docker Compose quick start and remove `make up` / `make status` as required setup commands
- [X] T015 [US1] Ensure `README.md` MCP client setup still documents the local Streamable HTTP endpoint and empty-database success behavior
- [X] T016 [US1] Add README troubleshooting entries in `README.md` for empty database, database not ready, MCP connection failure, config changes requiring recreate/restart, and blocked upstream collection

**Checkpoint**: User Story 1 is independently complete when the README normal-user path works without `make` and its Docker docs contract passes.

---

## Phase 4: User Story 2 - Trust the Public Automation Surface (Priority: P2)

**Goal**: Public workflows, scripts, docs, and tests show CI-only verification plus public release artifacts, with no private server deployment.

**Independent Test**: A search of active public surfaces `README.md`, `.github/`, `scripts/`, and `docs/` finds no Oracle/private deployment workflow, secret, host path, SSH deploy step, or private rollback runbook; `tests/docker` asserts that tests do not require private deployment artifacts to exist.

### Tests for User Story 2

- [X] T017 [P] [US2] Add CI-only assertions in `tests/docker/test_oss_readiness_contract.py` or `tests/docker/test_release_workflow_contract.py` for `.github/workflows/ci-cd.yml`
- [X] T018 [P] [US2] Add private-deploy absence assertions in `tests/docker/test_oss_readiness_contract.py` for active public surfaces `README.md`, `.github/`, `scripts/`, and `docs/`
- [X] T019 [P] [US2] Add release artifact assertions in `tests/docker/test_release_workflow_contract.py` for `.github/workflows/release.yml`

### Implementation for User Story 2

- [X] T020 [US2] Remove `changes` and `deploy-oracle` jobs from `.github/workflows/ci-cd.yml` so normal CI runs verification only
- [X] T021 [US2] Delete private deploy scripts in `scripts/deploy/oracle-compose-deploy.sh` and `scripts/deploy/should-deploy-oracle.sh`
- [X] T022 [US2] Delete Oracle/private deploy documentation in `docs/ORACLE_CLOUD_DEPLOY.md` and remove any stale Oracle deployment references from `docs/PRD.md`, `docs/TRD.md`, and `docs/ARCHITECTURE.md`
- [X] T023 [US2] Keep README badges in `README.md` and update badge labels/reference text so CI is verification-only and release is public artifact publishing
- [X] T024 [US2] Remove stale deployment helper references from `tests/docker/deploy_contract_helpers.py` if no remaining public-boundary tests use it

**Checkpoint**: User Story 2 is independently complete when public automation tests pass and no active private deployment traces remain.

---

## Phase 5: User Story 3 - Understand Data Counts and Safety Boundaries (Priority: P3)

**Goal**: A user can understand run counters, `job_id` deduplication, and Upwork-related safety boundaries from `README.md`.

**Independent Test**: README contract tests prove `seen`, `inserted`, `skipped`, `job_id` deduplication, authorized-data boundary, and non-goals are documented.

### Tests for User Story 3

- [X] T025 [P] [US3] Add counter-definition assertions in `tests/docker/test_docs_contract.py` for `seen`, `inserted`, `skipped`, and `job_id` deduplication in `README.md`
- [X] T026 [P] [US3] Add safety-boundary assertions in `tests/docker/test_docs_contract.py` or `tests/docker/test_oss_readiness_contract.py` for no affiliation, authorized data only, no credential guidance, no raw private payload persistence, no proposal generation, and no auto-apply

### Implementation for User Story 3

- [X] T027 [US3] Add a run counter explanation to `README.md` defining `seen`, `inserted`, `skipped`, and `job_id` deduplication
- [X] T028 [US3] Tighten the safety boundary section in `README.md` for Upwork non-affiliation, authorized-data use, no cookies/sessions/proxies/bypass guidance, no raw private payload persistence, no proposal/message generation, and no auto-apply
- [X] T029 [US3] Ensure optional developer docs referenced from `README.md` do not replace the README counter or safety explanations in `README.md`

**Checkpoint**: User Story 3 is independently complete when README explains counters and safety boundaries without requiring a separate data-model document.

---

## Phase 6: Polish & Cross-Cutting Verification

**Purpose**: Ensure the clarified spec, plan, public contracts, docs, and tests agree.

- [X] T030 [P] Update `AGENTS.md` and developer reference links in `README.md` so developer docs are optional and not part of the normal-user path
- [X] T031 [P] Run `uv run --extra dev pytest -q tests/docker` for `tests/docker`
- [X] T032 [P] Run the private-deployment inventory command from `specs/001-public-repo-readiness/quickstart.md` against `README.md`, `.github/`, `scripts/`, and `docs/`
- [X] T033 Run `make quality` from `Makefile`
- [X] T034 Run `make smoke` from `Makefile`
- [X] T035 Run `make e2e-smoke` from `Makefile`
- [X] T036 Update `specs/001-public-repo-readiness/quickstart.md` if verification commands or public-surface checks changed during implementation

---

## Dependencies & Execution Order

### Phase Dependencies

- **Phase 1 Setup**: No dependencies.
- **Phase 2 Foundational**: Depends on Phase 1 inventory and defines target tests for all stories.
- **Phase 3 US1**: Depends on Phase 2. Delivers MVP README-first local operation.
- **Phase 4 US2**: Depends on Phase 2. Can run after or in parallel with US1 if file conflicts are coordinated.
- **Phase 5 US3**: Depends on Phase 2. Best done after US1 because it edits the same `README.md`.
- **Phase 6 Polish**: Depends on selected user stories being complete.

### User Story Dependencies

- **US1 (P1)**: MVP. No dependency on US2 or US3 after Phase 2.
- **US2 (P2)**: No functional dependency on US1, but may touch shared README badges/reference text.
- **US3 (P3)**: No functional dependency on US2, but should coordinate with US1 because both edit README.

### Parallel Opportunities

- T001, T002, and T003 can run in parallel.
- T005 and T006 can run in parallel with T004; T007 should run after obsolete test files are identified.
- T008, T009, and T010 can run in parallel before US1 README edits.
- T017, T018, and T019 can run in parallel before US2 workflow/script/doc edits.
- T025 and T026 can run in parallel before US3 README edits.
- T031 and T032 can run in parallel after implementation; T033-T035 should run after narrow tests pass.

---

## Parallel Example: User Story 1

```text
Task: "T008 Add README quick-start assertions in tests/docker/test_docs_contract.py"
Task: "T009 Add environment-comment assertions in tests/docker/test_docs_contract.py"
Task: "T010 Add operation-command assertions in tests/docker/test_docs_contract.py"
```

## Parallel Example: User Story 2

```text
Task: "T017 Add CI-only assertions for .github/workflows/ci-cd.yml"
Task: "T018 Add private-deploy absence assertions for README.md, .github/, scripts/, and docs/"
Task: "T019 Add release artifact assertions for .github/workflows/release.yml"
```

## Parallel Example: User Story 3

```text
Task: "T025 Add counter-definition assertions in tests/docker/test_docs_contract.py"
Task: "T026 Add safety-boundary assertions in tests/docker/test_docs_contract.py or tests/docker/test_oss_readiness_contract.py"
```

---

## Implementation Strategy

### MVP First (User Story 1 Only)

1. Complete Phase 1 and Phase 2.
2. Complete Phase 3 for README-first Docker Compose operation.
3. Run `uv run --extra dev pytest -q tests/docker` for `tests/docker`.
4. Stop and validate that a normal user can follow README without Make.

### Incremental Delivery

1. US1: README-first Docker Compose path.
2. US2: CI-only and private deployment removal.
3. US3: Counter definitions and safety boundary.
4. Polish: full verification and public-surface grep.

### Verification Scope

- Required narrow check: `uv run --extra dev pytest -q tests/docker`
- Required broad checks when implementation completes: `make quality`, `make smoke`, `make e2e-smoke`
- Out of scope: `make live-smoke`

## Notes

- Do not change `src/work_feed_mcp/` runtime, schema, MCP tool semantics, worker health semantics, or blocked/upstream retry behavior for this feature.
- Keep `release.yml` scoped to public artifact publishing only.
- Private deployment may continue outside this repository as a private/local layer, but not through public workflows, scripts, docs, or tests.
