.PHONY: up down restart status logs config quality smoke e2e-smoke mcp-smoke docker-compose-config live-smoke clean

QUERY ?=
APP_DB ?= $(CURDIR)/data/work-feed.sqlite
MAX_PAGES ?= 1
PAGE_SIZE ?= 50
FIXTURE ?= tests/fixtures/visitor_job_search_response.json
SMOKE_OUT ?= /tmp/work-feed-fixture.jsonl
E2E_DB ?= /tmp/work-feed-e2e.sqlite
E2E_JSONL ?= /tmp/work-feed-e2e.jsonl
MCP_URL ?= http://127.0.0.1:8000/mcp

up:
	docker compose up -d

down:
	docker compose down

restart:
	docker compose up -d --force-recreate

status:
	docker compose ps

logs:
	docker compose logs -f work-feed-worker work-feed-mcp

config: docker-compose-config

quality:
	uv run --extra dev ruff format --check .
	uv run --extra dev ruff check .
	uv run --extra dev mypy src
	uv run --extra dev pytest -q

smoke:
	uv run --extra dev work-feed collect --fixture $(FIXTURE) > $(SMOKE_OUT)
	python -c 'import json,sys; [json.loads(line) for line in sys.stdin if line.strip()]' < $(SMOKE_OUT)

e2e-smoke:
	rm -f $(E2E_DB) $(E2E_JSONL)
	uv run --extra dev work-feed collect --fixture $(FIXTURE) > $(E2E_JSONL)
	uv run --extra dev work-feed ingest --db $(E2E_DB) --input $(E2E_JSONL) $(if $(QUERY),--query "$(QUERY)",)
	uv run --extra dev work-feed analytics summary --db $(E2E_DB)
	uv run --extra dev work-feed analytics skills --db $(E2E_DB)
	uv run --extra dev work-feed analytics clients --db $(E2E_DB)

mcp-smoke:
	uv run --extra dev work-feed mcp-smoke --url $(MCP_URL)

docker-compose-config:
	docker compose config >/tmp/work-feed-compose-config.yaml

live-smoke:
	@WORK_FEED_LIVE=1 uv run --extra dev work-feed collect --live $(if $(QUERY),--query "$(QUERY)",) --max-pages $(MAX_PAGES) --page-size $(PAGE_SIZE)


clean:
	rm -rf .pytest_cache .mypy_cache .ruff_cache src/*.egg-info
	find src tests -type d -name __pycache__ -prune -exec rm -rf {} +
