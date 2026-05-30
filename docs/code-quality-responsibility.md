# Code Quality Responsibility Guide

## Purpose and audience

This guide helps reviewers judge whether a file or function has the right responsibility
boundary. It is for code review and maintenance discussions in `work-feed-mcp`; it is not a
source-change plan.

Use it when a unit feels large, hard to test, hard to name, or likely to change for unrelated
reasons. Start with the general principles, then use the repository examples only to calibrate
judgment.

## Severity vocabulary

Use mixed rule strength: hard language for structural boundary violations, advisory language
for contextual tradeoffs.

| Severity | Review meaning | When to use |
| --- | --- | --- |
| **Must** | The current boundary blocks safe review or violates an existing architectural contract. | The unit has multiple independent reasons to change, crosses a declared layer boundary, hides side effects, or mixes incompatible abstraction levels. |
| **Should** | The boundary is workable now but carries clear maintenance risk. | The unit is mostly cohesive but combines several policies, has growing branch/error complexity, or is likely to become unstable with the next feature. |
| **May** | The boundary is acceptable as-is. | The unit is long because of cohesive mapping, adapter registration, schema declaration, SQL row conversion, or other single-purpose boilerplate. |

## Quick classification

| Outcome | Reviewer decision | Observable signals |
| --- | --- | --- |
| **split required** | Request a boundary change before accepting the design. | More than one reason to change; mixed transport/persistence/domain/presentation concerns; hard project boundary violation; hidden side effects. |
| **caution** | Accept only with a clear rationale, or mark as a watch point. | One main purpose remains, but orchestration, retry, history, transaction, or error policy are tightly coupled. |
| **acceptable** | Do not request a split only because the code is long. | The code has one abstraction level, one reason to change, and tests/reviewers can reason about it as one unit. |

## General principles

### 1. One reason to change

A good unit has one primary reason to change. A service orchestration function may coordinate
steps, but it becomes risky when collection policy, persistence policy, retry policy,
transaction policy, and error-report formatting all change in the same place for unrelated
reasons.

Reviewer question: **Which future change would force this unit to change, and is that reason
singular?**

### 2. One abstraction level per unit

A unit should not mix high-level workflow with low-level details unless those details are the
unit's actual purpose. A mapper may handle field-by-field conversion; an orchestrator should not
also own raw transport parsing or SQL shape decisions.

Reviewer question: **Are the lines in this unit all speaking at the same level of abstraction?**

### 3. Boundary contracts outrank convenience

Existing architecture contracts are hard review boundaries. In this repository, import-linter
contracts define layer separation for domain, persistence, integration, service, MCP, runtime,
and CLI code. Convenience does not justify crossing those contracts.

Reviewer question: **Would this import or side effect violate a declared layer boundary?**

### 4. Test burden exposes responsibility burden

If a single test must set up unrelated transport, retry, DB, run-history, and formatting
conditions to verify one behavior, the production unit may be carrying too many responsibilities.

Reviewer question: **Does one behavior require a wide, unrelated test fixture to prove?**

### 5. Length is evidence, not a verdict

Long code is acceptable when it is cohesive. Adapter registration, schema declaration, and
field mapping can be long because the domain shape is long. Penalize mixed reasons to change,
not line count by itself.

Reviewer question: **Is this long because the one job is verbose, or because several jobs are
entangled?**

## Red flags / anti-patterns

Use **Must** or **Should** severity when these signals are present:

- A function name describes one operation, but the body owns several policies.
- A service function performs low-level transport parsing or SQL construction that belongs in an
  integration or repository layer.
- A repository helper reaches upward into service, runtime, CLI, or MCP concepts.
- Error handling both controls the workflow and formats durable diagnostics in a way that would
  change for separate reasons.
- A new feature would require editing the same unit for collection behavior, persistence behavior,
  and presentation behavior.
- Tests for one branch need extensive setup for unrelated branches.
- A layer boundary is crossed because it is convenient rather than because the architecture permits it.

## Acceptable exceptions

Do not request a split solely because these units are long:

- **Cohesive mappers**: one raw shape is converted into one domain shape.
- **Adapter registration**: many small handlers are registered with a framework in one place.
- **Schema declarations**: SQL table/index declarations are verbose but share one schema purpose.
- **Repository row conversion**: a query helper and row formatter can stay together when they are one
  persistence-facing concern.
- **Configuration tables or constants**: a single contract may require a long list of fields, keys,
  or options.

The exception stops applying when the unit starts gaining unrelated policy decisions, hidden side
effects, or cross-layer authority.

## Review checklist

Use this checklist as a quick review pass:

1. Name the unit's one primary responsibility.
2. List the reasons it might change in the next few PRs.
3. Check whether those reasons belong to the same layer and abstraction level.
4. Check whether existing import-linter or project boundary contracts allow the dependency direction.
5. Decide whether the evidence supports **split required**, **caution**, or **acceptable**.
6. If the answer is **caution**, record the specific growth signal rather than prescribing a code move.
7. If the answer is **acceptable**, state why cohesion outweighs length.

## Repo-calibrated examples

These examples calibrate review judgment against the current repository. They are not instructions
to change the cited code.

### `src/work_feed_mcp/services/scheduled_collection.py:118-272`

**Label:** Calibration example
**Classification:** **Should / caution** hotspot

`collect_scheduled()` coordinates query resolution, run creation, retry wiring, job validation,
ingestion, run-result persistence, failure recording, totals, commits, rollback, and connection
closure in one function. That is credible caution evidence because several policies converge in one
orchestration unit.

The current classification is **caution**, not automatic **split required**, because the function is
still part of one scheduled-collection use case and tests document its partial-failure behavior. A
similar unit escalates to **Must / split required** when unrelated feature changes repeatedly require
editing separate policies in the same function or when tests become too broad to isolate one behavior.

This example calibrates review judgment; it is not a standalone refactoring backlog item.

### `src/work_feed_mcp/integrations/upwork/normalize.py:56-124`

**Label:** Calibration example
**Classification:** **May / acceptable** cohesive mapper

`normalize_result()` is long, but its purpose is narrow: normalize one Upwork result shape into one
`Job` model. Field extraction, required identity checks, budget conversion, and skill extraction all
serve that one mapping responsibility.

This is acceptable long code unless it starts owning transport behavior, persistence behavior, or
application orchestration.

This example calibrates review judgment; it is not a standalone refactoring backlog item.

### `src/work_feed_mcp/mcp_server/server.py:13-85`

**Label:** Calibration example
**Classification:** **May / acceptable** adapter registration

`build_server()` registers MCP tools and delegates behavior to `work_feed_mcp.mcp_server.tools`.
The repeated local functions are framework-facing registration boilerplate. Length alone does not
show mixed domain responsibility.

This stays acceptable while the handlers remain thin and delegate to services/tools rather than
embedding business logic.

This example calibrates review judgment; it is not a standalone refactoring backlog item.

### `src/work_feed_mcp/services/health.py:15-78`

**Label:** Calibration example
**Classification:** **May / acceptable, monitor growth**

`health_check()` currently answers one runtime-readiness question: is this role ready enough for a
container/local health check? DB existence, schema readiness, config readiness, and optional MCP HTTP
reachability are related to that role-readiness purpose.

Monitor this area if role-specific checks grow into independent policies. At that point, the review
question should be whether the code still has one readiness responsibility or has accumulated several
role-specific workflows.

This example calibrates review judgment; it is not a standalone refactoring backlog item.

### `src/work_feed_mcp/repositories/jobs.py:9-88`

**Label:** Calibration example
**Classification:** **May / acceptable** repository query and row mapping

The public helpers query jobs, filter by title/skill, fetch skills, and return JSON-safe row dicts.
Those details belong to one repository concern: converting SQLite rows into query results for callers.

Do not treat this as a responsibility issue just because multiple helper functions live together.
A responsibility problem would appear if this repository started importing service/runtime/MCP concerns
or making application policy decisions.

This example calibrates review judgment; it is not a standalone refactoring backlog item.

### `pyproject.toml:48-104`

**Label:** Boundary reference
**Classification:** **Must** architectural boundary guard

The import-linter contracts are hard project boundaries. They keep domain independent from
infrastructure, keep persistence below application interfaces, keep Upwork integration below app
interfaces, prevent services from depending on interface adapters, and keep MCP independent from CLI.

A proposed source change that violates these contracts should be treated as **Must / split required**
or redesigned unless the architecture contract itself is intentionally changed through a separate
planning decision.

This example calibrates review judgment; it is not a standalone refactoring backlog item.

### `Makefile:30-41`

**Label:** Boundary reference
**Classification:** verification reference

The quality targets define the normal verification surface: formatting, lint, typecheck,
import-linter architecture checks, tests, and coverage. Use these commands to validate later source
changes, but do not treat this guide as a reason to run live collection or change runtime behavior.

This example calibrates review judgment; it is not a standalone refactoring backlog item.

## Non-goals

- This guide is not a refactoring backlog or implementation plan.
- This guide does not require splitting every long function or file.
- This guide does not override import-linter, ruff, mypy, pytest, or project product boundaries.
- This guide does not justify behavior, API, schema, live collection, ranking, proposal, UI, or
  notification changes by itself.
- This guide does not decide future extraction targets. It only defines review evidence and severity.
