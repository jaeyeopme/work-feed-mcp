.PHONY: format-check lint typecheck test quality smoke clean

PYTHON ?= python
DB ?= /tmp/upwork-ingest-smoke.sqlite
FIXTURE ?= tests/fixtures/collector_jobs_valid.jsonl

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
	rm -f $(DB)
	printf '%s\n' '{"source":"upwork","id":"~021111","title":"Python data pipeline","description":"Build ingestion pipelines","url":"https://www.upwork.com/jobs/~021111","skills":["Python","SQLite"],"hourly_min":40,"hourly_max":70}' > /tmp/upwork-ingest-smoke.jsonl
	PYTHONPATH=src:../../src $(PYTHON) -m upwork_ingest ingest --db $(DB) --input /tmp/upwork-ingest-smoke.jsonl --query python
	$(PYTHON) -c "import sqlite3; con=sqlite3.connect('$(DB)'); assert con.execute('select count(*) from jobs').fetchone()[0] > 0; assert con.execute('select count(*) from ingest_runs').fetchone()[0] == 1; con.close()"

clean:
	rm -rf .pytest_cache .mypy_cache .ruff_cache src/*.egg-info
	find . -type d -name __pycache__ -prune -exec rm -rf {} +
