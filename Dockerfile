FROM python:3.13-slim

ENV PYTHONDONTWRITEBYTECODE=1 \
    PYTHONUNBUFFERED=1 \
    UPWORK_COLLECTOR_DB=/data/upwork.sqlite

WORKDIR /app
COPY pyproject.toml README.md ./
COPY src ./src
COPY tests/fixtures ./tests/fixtures
RUN pip install --no-cache-dir .
RUN mkdir -p /data
VOLUME ["/data"]

CMD ["upwork-app", "worker"]
