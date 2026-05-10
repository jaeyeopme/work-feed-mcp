.PHONY: collector-quality collector-smoke collector-live-smoke quality smoke live-smoke clean

QUERY ?= python
MAX_PAGES ?= 1
PAGE_SIZE ?= 50
FIXTURE ?= tests/fixtures/visitor_job_search_response.json
SMOKE_OUT ?= /tmp/upwork-collector-fixture.jsonl

collector-quality:
	$(MAKE) -C packages/collector quality

collector-smoke:
	$(MAKE) -C packages/collector smoke FIXTURE=$(FIXTURE) SMOKE_OUT=$(SMOKE_OUT)

collector-live-smoke:
	$(MAKE) -C packages/collector live-smoke QUERY="$(QUERY)" MAX_PAGES=$(MAX_PAGES) PAGE_SIZE=$(PAGE_SIZE)

quality: collector-quality

smoke: collector-smoke

live-smoke: collector-live-smoke

clean:
	$(MAKE) -C packages/collector clean
