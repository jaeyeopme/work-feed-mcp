from __future__ import annotations

import sqlite3
from contextlib import closing
from pathlib import Path

import pytest

from work_feed_mcp.services.analytics import AnalyticsServiceError, query_database


def test_query_database_maps_missing_database_to_service_error(tmp_path: Path) -> None:
    missing_db = tmp_path / "missing.sqlite"

    with pytest.raises(AnalyticsServiceError, match="analytics database unavailable"):
        query_database(str(missing_db), "summary")


def test_query_database_rejects_unknown_query_name(tmp_path: Path) -> None:
    db = tmp_path / "work-feed.sqlite"
    with closing(sqlite3.connect(db)):
        pass

    with pytest.raises(ValueError, match="unknown analytics query: unknown"):
        query_database(str(db), "unknown")


def test_query_database_rejects_invalid_jobs_limit(tmp_path: Path) -> None:
    db = tmp_path / "work-feed.sqlite"
    with closing(sqlite3.connect(db)) as connection:
        connection.execute(
            """
            CREATE TABLE jobs (
              job_id TEXT PRIMARY KEY,
              source TEXT NOT NULL,
              title TEXT NOT NULL,
              description TEXT NULL,
              url TEXT NULL,
              posted_at TEXT NULL,
              job_type TEXT NULL,
              contractor_tier TEXT NULL,
              hourly_min REAL NULL,
              hourly_max REAL NULL,
              fixed_amount REAL NULL,
              raw_id TEXT NULL,
              content_hash TEXT NOT NULL,
              first_seen_at TEXT NOT NULL,
              created_at TEXT NOT NULL
            )
            """
        )

    with pytest.raises(ValueError, match="limit must be a positive integer"):
        query_database(str(db), "jobs", limit=0)
