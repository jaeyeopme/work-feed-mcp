from __future__ import annotations

from pathlib import Path

from upwork_app.db.connection import connect_worker
from upwork_app.repositories import collector_control
from upwork_app.runtime.config import RuntimeSettings
from upwork_app.services.health import health_check


def test_health_reports_missing_db(tmp_path: Path) -> None:
    result = health_check(str(tmp_path / "missing.sqlite"), role="worker")
    assert result["ok"] is False
    assert result["reason"] == "db_missing"
    assert result["checks"]["db_exists"] is False


def test_health_reports_ready_after_worker_bootstrap(tmp_path: Path) -> None:
    db = tmp_path / "upwork.sqlite"
    with connect_worker(str(db)) as connection:
        collector_control.seed_config(
            connection, RuntimeSettings(db_path=str(db)).persisted_defaults()
        )
        connection.commit()

    result = health_check(str(db), role="mcp")
    assert result["ok"] is True
    assert result["status"] == "ready"
    assert result["checks"]["schema"] == "ready"
    assert result["checks"]["config"] == "ready"
