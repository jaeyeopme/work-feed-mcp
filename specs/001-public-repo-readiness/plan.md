# Implementation Plan: Public Repository Readiness

**Branch**: `main` | **Date**: 2026-05-30 | **Spec**: [spec.md](./spec.md)

**Input**: Feature specification from `specs/001-public-repo-readiness/spec.md`

**Note**: This plan was produced during the Spec Kit planning workflow.

## Summary

Make the public repository understandable, runnable, and safe for a new local Docker/MCP user. The implementation will make README the complete normal-user source of truth, keep developer docs as optional references, switch the documented quick start to standard Docker Compose, keep Make as optional wrappers, delete Oracle/private deploy scripts/docs/workflow expectations from the public surface, keep CI verification-only, document run counters and `job_id` deduplication, and preserve GHCR/GitHub Release automation only as public artifact publishing.

## Technical Context

**Language/Version**: Python >=3.11 for repository tests; no runtime Python behavior changes planned

**Primary Dependencies**: Existing Docker Compose, GitHub Actions, pytest, ruff, mypy, import-linter; no new production dependency planned

**Storage**: Existing SQLite runtime documented only; no schema or data retention change

**Testing**: Documentation/workflow contract tests under `tests/docker`, plus `make quality`, `make smoke`, `make e2e-smoke` when practical

**Target Platform**: Public clone running local Docker Compose and connecting local MCP clients

**Project Type**: Docker/MCP-first local data engine with public documentation and CI/release automation

**Performance Goals**: First-time user can complete README startup and status check in under 10 minutes; no runtime performance changes planned

**Constraints**: README-first normal-user documentation; developer docs may remain optional but cannot be required for normal usage; active public docs/workflows/scripts/tests must not include or require private server deployment traces; live collection remains explicit opt-in and separate from fixture/local evidence; no credential/session/proxy/bypass guidance

**Scale/Scope**: Public repository readiness only: documentation, example environment comments, CI/release workflow surfaces, scripts, and contract tests

## Constitution Check

*GATE: Must pass before Phase 0 research. Re-check after Phase 1 design.*

- Scope gate: PASS. The feature keeps the Docker/MCP data-engine scope and only changes public documentation, automation, and tests around that scope.
- Secret-safety gate: PASS. The plan removes private deployment secret references from active public surfaces and does not add credential, cookie, session, proxy, token, or raw upstream payload guidance.
- Layer gate: PASS. No application-layer code changes are planned. Test updates stay in documentation/workflow contract tests.
- SQLite authority gate: PASS. No schema, MCP read/control behavior, or worker authority change is planned.
- Verification gate: PASS. Narrow contract tests will be updated and run first; broader fixture/local gates will be run when implementation completes. Live evidence remains out of scope.

Post-design re-check: PASS. Phase 0 and Phase 1 artifacts preserve the same boundaries and do not introduce runtime, schema, MCP, or live-collection changes.

## Project Structure

### Documentation (this feature)

```text
specs/001-public-repo-readiness/
├── spec.md
├── plan.md
├── research.md
├── data-model.md
├── quickstart.md
├── contracts/
│   └── public-surface.md
└── tasks.md             # Created later by /speckit-tasks
```

### Source Code (repository root)

```text
README.md                 # Primary normal-user documentation
.env.example              # Copyable runtime configuration comments
compose.yaml              # Existing Docker Compose runtime, unchanged unless docs reveal mismatch
Makefile                  # Convenience wrappers, not primary user path
.github/workflows/ci-cd.yml
.github/workflows/release.yml  # Public artifact publishing only
scripts/deploy/           # Oracle/private deployment scripts removed
docs/                     # Optional developer references only, not required for normal use
tests/docker/             # Public-readiness, docs, compose, release, and workflow contract tests
```

**Structure Decision**: Keep application source unchanged. Update public docs and automation surfaces, delete or rewrite private deployment contract tests, then update `tests/docker` contracts to match the public repository policy.

## Complexity Tracking

> **Fill ONLY if Constitution Check has violations that must be justified**

No constitution violations.
