from __future__ import annotations

from pathlib import Path

from upwork_app.db.connection import connect_worker
from upwork_app.services import job_queries


def test_jobs_get_missing_returns_not_found(tmp_path: Path) -> None:
    db = tmp_path / "upwork.sqlite"
    connect_worker(str(db)).close()
    result = job_queries.jobs_get(str(db), job_id="missing")
    assert result == {"ok": False, "error": "not_found", "job_id": "missing"}
