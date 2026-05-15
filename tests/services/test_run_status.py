from __future__ import annotations

from pathlib import Path

from work_feed_mcp.db.connection import connect_worker
from work_feed_mcp.services.run_status import run_status


def test_run_status_empty_schema_returns_empty(tmp_path: Path) -> None:
    db = tmp_path / "work-feed.sqlite"
    connect_worker(str(db)).close()
    result = run_status(str(db))
    assert result["ok"] is True
    assert result["status"] == "empty"
    assert result["last_run"] is None
