.PHONY: quality smoke e2e-smoke docker-compose-config live-smoke collect-live-once clean

QUERY ?=
APP_DB ?= $(CURDIR)/data/upwork.sqlite
MAX_PAGES ?= 1
PAGE_SIZE ?= 50
FIXTURE ?= tests/fixtures/visitor_job_search_response.json
SMOKE_OUT ?= /tmp/upwork-app-fixture.jsonl
E2E_DB ?= /tmp/upwork-e2e.sqlite
E2E_JSONL ?= /tmp/upwork-e2e.jsonl

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
	uv run --extra dev upwork-app-ingest --db $(E2E_DB) --input $(E2E_JSONL) $(if $(QUERY),--query "$(QUERY)",)
	uv run --extra dev upwork-app-analytics summary --db $(E2E_DB)
	uv run --extra dev upwork-app-analytics skills --db $(E2E_DB)
	uv run --extra dev upwork-app-analytics clients --db $(E2E_DB)

docker-compose-config:
	docker compose config >/tmp/upwork-compose-config.yaml

live-smoke:
	@UPWORK_COLLECTOR_LIVE=1 uv run --extra dev upwork-app-collect --live $(if $(QUERY),--query "$(QUERY)",) --max-pages $(MAX_PAGES) --page-size $(PAGE_SIZE)

collect-live-once:
	@QUERY="$(QUERY)" APP_DB="$(APP_DB)" MAX_PAGES="$(MAX_PAGES)" PAGE_SIZE="$(PAGE_SIZE)" ./scripts/collect_live_once.sh

clean:
	rm -rf .pytest_cache .mypy_cache .ruff_cache src/*.egg-info
	find src tests -type d -name __pycache__ -prune -exec rm -rf {} +
