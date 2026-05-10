.PHONY: format-check lint typecheck test quality smoke live-smoke clean

PYTHON ?= python
QUERY ?= python
MAX_PAGES ?= 1
PAGE_SIZE ?= 50
FIXTURE ?= tests/fixtures/visitor_job_search_response.json
SMOKE_OUT ?= /tmp/upwork-collector-fixture.jsonl

format-check:
	ruff format --check .

lint:
	ruff check .

typecheck:
	mypy src

test:
	pytest

quality: format-check lint typecheck test

smoke:
	PYTHONPATH=src $(PYTHON) -m upwork_collector collect --fixture $(FIXTURE) > $(SMOKE_OUT)
	$(PYTHON) -c 'import json,sys; [json.loads(line) for line in sys.stdin if line.strip()]' < $(SMOKE_OUT)

live-smoke:
	PYTHONPATH=src UPWORK_COLLECTOR_LIVE=1 $(PYTHON) -m upwork_collector live-smoke --query "$(QUERY)" --max-pages $(MAX_PAGES) --page-size $(PAGE_SIZE)

clean:
	rm -rf .pytest_cache .mypy_cache .ruff_cache src/*.egg-info
	find . -type d -name __pycache__ -prune -exec rm -rf {} +
