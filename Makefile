.PHONY: dev run quality smoke e2e-smoke live-smoke clean

QUERY ?= python
APP_HOST ?= 127.0.0.1
APP_PORT ?= 8000
APP_DB ?= /tmp/upwork.sqlite
MAX_PAGES ?= 1
PAGE_SIZE ?= 50
FIXTURE ?= tests/fixtures/visitor_job_search_response.json
SMOKE_OUT ?= /tmp/upwork-app-fixture.jsonl
E2E_DB ?= /tmp/upwork-e2e.sqlite
E2E_JSONL ?= /tmp/upwork-e2e.jsonl

dev:
	UPWORK_APP_DB=$(APP_DB) uv run --extra dev uvicorn upwork_app.main:app --host $(APP_HOST) --port $(APP_PORT) --reload

run:
	UPWORK_APP_DB=$(APP_DB) uv run --extra dev uvicorn upwork_app.main:app --host $(APP_HOST) --port $(APP_PORT)

quality:
	uv run --extra dev ruff format --check .
	uv run --extra dev ruff check .
	uv run --extra dev mypy src
	uv run --extra dev pytest -q

smoke:
	uv run --extra dev upwork-app-collect --fixture $(FIXTURE) > $(SMOKE_OUT)
	python -c 'import json,sys; [json.loads(line) for line in sys.stdin if line.strip()]' < $(SMOKE_OUT)

e2e-smoke:
	rm -f $(E2E_DB) $(E2E_JSONL)
	uv run --extra dev upwork-app-collect --fixture $(FIXTURE) > $(E2E_JSONL)
	uv run --extra dev upwork-app-ingest --db $(E2E_DB) --input $(E2E_JSONL) --query "$(QUERY)"
	uv run --extra dev upwork-app-analytics summary --db $(E2E_DB)
	uv run --extra dev upwork-app-analytics skills --db $(E2E_DB)
	uv run --extra dev upwork-app-analytics clients --db $(E2E_DB)

live-smoke:
	UPWORK_COLLECTOR_LIVE=1 uv run --extra dev upwork-app-collect --live --query "$(QUERY)" --max-pages $(MAX_PAGES) --page-size $(PAGE_SIZE)

clean:
	rm -rf .pytest_cache .mypy_cache .ruff_cache src/*.egg-info
	find src tests -type d -name __pycache__ -prune -exec rm -rf {} +
