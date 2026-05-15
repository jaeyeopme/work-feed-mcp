"""Application configuration."""

from __future__ import annotations

import os
from dataclasses import dataclass


@dataclass(frozen=True, slots=True)
class Settings:
    """Runtime settings for CLI collection and ingestion."""

    default_db_path: str = "/tmp/work-feed.sqlite"
    allow_live_collect: bool = False


def get_settings() -> Settings:
    return Settings(
        default_db_path=os.environ.get("WORK_FEED_DB", "/tmp/work-feed.sqlite"),
        allow_live_collect=os.environ.get("WORK_FEED_LIVE") == "1",
    )
