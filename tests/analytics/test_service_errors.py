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
