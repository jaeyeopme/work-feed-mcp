"""FastAPI application entrypoint."""

from __future__ import annotations

from fastapi import FastAPI

from upwork_app.api.routes import analytics, collect, health, ingest

app = FastAPI(title="Upwork Job Discovery API", version="0.1.0")
app.include_router(health.router)
app.include_router(collect.router)
app.include_router(ingest.router)
app.include_router(analytics.router)
