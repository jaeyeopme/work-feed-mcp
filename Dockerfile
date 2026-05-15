FROM python:3.13-slim

ENV PYTHONDONTWRITEBYTECODE=1 \
    PYTHONUNBUFFERED=1 \
    UPWORK_COLLECTOR_DB=/data/upwork.sqlite \
    PATH="/app/.venv/bin:$PATH"

WORKDIR /app
COPY pyproject.toml uv.lock README.md ./
COPY src ./src
COPY tests/fixtures ./tests/fixtures
RUN pip install --no-cache-dir uv \
    && uv sync --frozen --no-dev --compile-bytecode
RUN mkdir -p /data
VOLUME ["/data"]

CMD ["upwork-app", "worker"]
