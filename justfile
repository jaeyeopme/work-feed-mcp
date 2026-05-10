set dotenv-load := true

query := env_var_or_default("QUERY", "python")
app_host := env_var_or_default("APP_HOST", "127.0.0.1")
app_port := env_var_or_default("APP_PORT", "8000")
app_db := env_var_or_default("UPWORK_APP_DB", "/tmp/upwork.sqlite")
fixture := env_var_or_default("FIXTURE", "packages/collector/tests/fixtures/visitor_job_search_response.json")
smoke_out := env_var_or_default("SMOKE_OUT", "/tmp/upwork-app-fixture.jsonl")
e2e_db := env_var_or_default("E2E_DB", "/tmp/upwork-e2e.sqlite")
e2e_jsonl := env_var_or_default("E2E_JSONL", "/tmp/upwork-e2e.jsonl")

_default:
    just --list

# Run the FastAPI dev server with reload.
dev:
    UPWORK_APP_DB={{app_db}} uv run --extra dev uvicorn upwork_app.main:app --host {{app_host}} --port {{app_port}} --reload

# Run the FastAPI server without reload.
run:
    UPWORK_APP_DB={{app_db}} uv run --extra dev uvicorn upwork_app.main:app --host {{app_host}} --port {{app_port}}

# Run root app formatting, linting, typing, and tests.
quality:
    uv run --extra dev ruff format --check .
    uv run --extra dev ruff check .
    uv run --extra dev mypy src
    uv run --extra dev pytest -q

# Run all compatibility checks, including legacy packages.
all-quality:
    make quality

# Run jscpd with project ignores.
dupe:
    npx jscpd --reporters ai --gitignore --min-lines 10 --ignore "**/.venv/**,**/.mypy_cache/**,**/.pytest_cache/**,**/.ruff_cache/**,**/__pycache__/**,**/*.egg-info/**,**/uv.lock,.omx/**" .

# Run fixture-only app smoke.
smoke:
    uv run --extra dev upwork-app-collect --fixture {{fixture}} > {{smoke_out}}
    python -c 'import json,sys; [json.loads(line) for line in sys.stdin if line.strip()]' < {{smoke_out}}

# Run fixture collect -> ingest -> analytics locally.
e2e:
    rm -f {{e2e_db}} {{e2e_jsonl}}
    uv run --extra dev upwork-app-collect --fixture {{fixture}} > {{e2e_jsonl}}
    uv run --extra dev upwork-app-ingest --db {{e2e_db}} --input {{e2e_jsonl}} --query "{{query}}"
    uv run --extra dev upwork-app-analytics summary --db {{e2e_db}}
    uv run --extra dev upwork-app-analytics skills --db {{e2e_db}}
    uv run --extra dev upwork-app-analytics clients --db {{e2e_db}}

# Run all local smoke checks, including legacy compatibility.
all-smoke:
    make smoke

# Run tests only.
test:
    uv run --extra dev pytest -q

# Format code.
fmt:
    uv run --extra dev ruff format .
    uv run --extra dev ruff check . --fix

# Remove local caches.
clean:
    make clean
