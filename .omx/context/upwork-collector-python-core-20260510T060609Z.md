# Context Snapshot: upwork-collector Python scraper core

## Task statement
Run `$ralplan` from `/Users/jaeyeop/Workspace/up-cli` for a new project at `/Users/jaeyeop/Workspace/upwork-collector`, using the Deep Interview spec as the authority, and produce plan/test-spec artifacts before any implementation.

## Desired outcome
A reviewed PRD and test specification for a clean Python-only Upwork scraper core that can later be implemented with TDD.

## Known facts / evidence
- `/Users/jaeyeop/Workspace/up-cli` currently has no `AGENTS.md` and no `.omx/specs/deep-interview-agent-misalignment-control.md`.
- The matching Deep Interview spec was found at `/Users/jaeyeop/Workspace/upfeed/.omx/specs/deep-interview-agent-misalignment-control.md`.
- The target project `/Users/jaeyeop/Workspace/upwork-collector` does not yet exist.
- Legacy reference scraper exists at `/Users/jaeyeop/Workspace/upwork-scraper/scraper.py`.
- The legacy scraper uses `curl_cffi.requests`, Upwork visitor token cookie fetch, GraphQL job search POST, Webshare proxy parsing, SQLite persistence, JSON snapshots, concurrent page fetches, and CLI flags.

## Constraints
- Produce plan/test-spec only; do not implement until approved.
- Python-only MVP; exclude Swift, UI/watcher app, upfeed scheduler/API/storage, and Go-native collector work.
- TDD-first with `pytest`, `ruff`, and `mypy`.
- JSONL stdout contract; stderr diagnostics only.
- Separate fixture verification from opt-in live verification.
- Do not expose credential/session material in commits, docs, or API payloads.
- Reference scraper.py but remove/separate SQLite, snapshots, and standalone durable state.

## Unknowns / open questions
- Package manager preference (`uv`, pip, Poetry) is not specified; plan should default to a lightweight `pyproject.toml` contract and can mention `uv` as optional.
- Live Upwork access/proxy credentials are not available and must remain outside artifacts.

## Likely touchpoints for future implementation
- `pyproject.toml`, `README.md`
- `src/upwork_collector/{cli.py,transport.py,graphql.py,normalize.py,credentials.py,errors.py,models.py}`
- `tests/{fixtures,test_normalize.py,test_credentials.py,test_cli_fixture.py,test_error_exit_codes.py,test_transport_contract.py}`
