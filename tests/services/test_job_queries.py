from __future__ import annotations

from pathlib import Path

import pytest

from work_feed_mcp.db.connection import connect_worker
from work_feed_mcp.services import job_queries


def test_jobs_get_missing_returns_not_found(tmp_path: Path) -> None:
    db = tmp_path / "work-feed.sqlite"
    connect_worker(str(db)).close()
    result = job_queries.jobs_get(str(db), job_id="missing")
    assert result == {"ok": False, "error": "not_found", "job_id": "missing"}


def test_job_query_limits_are_bounded(tmp_path: Path) -> None:
    db = tmp_path / "work-feed.sqlite"
    connect_worker(str(db)).close()

    for invalid in [0, -1, 101, True, 1.5]:
        with pytest.raises(ValueError):
            job_queries.jobs_recent(str(db), limit=invalid)
        with pytest.raises(ValueError):
            job_queries.jobs_search(str(db), title="python", limit=invalid)


def test_job_query_limits_validate_before_db_readiness(tmp_path: Path) -> None:
    missing_db = tmp_path / "missing.sqlite"

    with pytest.raises(ValueError):
        job_queries.jobs_recent(str(missing_db), limit=0)
    with pytest.raises(ValueError):
        job_queries.jobs_search(str(missing_db), title="python", limit=0)
