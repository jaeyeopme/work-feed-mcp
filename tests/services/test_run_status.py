from __future__ import annotations

from pathlib import Path

import pytest

from work_feed_mcp.db.connection import connect_worker
from work_feed_mcp.services.run_status import run_status


def test_run_status_empty_schema_returns_empty(tmp_path: Path) -> None:
    db = tmp_path / "work-feed.sqlite"
    connect_worker(str(db)).close()
    result = run_status(str(db))
    assert result["ok"] is True
    assert result["status"] == "empty"
    assert result["last_run"] is None


def test_run_status_limit_is_bounded(tmp_path: Path) -> None:
    db = tmp_path / "work-feed.sqlite"
    connect_worker(str(db)).close()

    for invalid in [0, -1, 101, True, 1.5]:
        with pytest.raises(ValueError):
            run_status(str(db), limit=invalid)
