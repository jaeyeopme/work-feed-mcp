"""FastAPI dependencies."""

from __future__ import annotations

from upwork_app.core.config import Settings, get_settings


def settings() -> Settings:
    return get_settings()
