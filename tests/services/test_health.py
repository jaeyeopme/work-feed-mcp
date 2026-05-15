from __future__ import annotations

from pathlib import Path

from tests.collector_db_helpers import create_ready_runtime_db
from tests.http_helpers import reachable_http_url

from work_feed_mcp.services.health import health_check


def test_health_reports_missing_db(tmp_path: Path) -> None:
    result = health_check(str(tmp_path / "missing.sqlite"), role="worker")
    assert result["ok"] is False
    assert result["reason"] == "db_missing"
    assert result["checks"]["db_exists"] is False


def test_health_reports_ready_after_worker_bootstrap(tmp_path: Path) -> None:
    db = tmp_path / "work-feed.sqlite"
    create_ready_runtime_db(db)

    result = health_check(str(db), role="mcp")
    assert result["ok"] is True
    assert result["status"] == "ready"
    assert result["checks"]["schema"] == "ready"
    assert result["checks"]["config"] == "ready"


def test_mcp_health_reports_unreachable_http(tmp_path: Path) -> None:
    db = tmp_path / "work-feed.sqlite"
    create_ready_runtime_db(db)

    result = health_check(str(db), role="mcp", http_url="http://127.0.0.1:9/mcp", http_timeout=0.2)

    assert result["ok"] is False
    assert result["status"] == "not_ready"
    assert result["reason"] == "http_unreachable"
    assert result["checks"]["http_reachable"] is False
    assert "http_error" in result["checks"]
    assert "mcp_protocol_ready" not in result["checks"]


def test_mcp_health_reports_reachable_http(tmp_path: Path) -> None:
    db = tmp_path / "work-feed.sqlite"
    create_ready_runtime_db(db)

    with reachable_http_url(status=404) as url:
        result = health_check(str(db), role="mcp", http_url=url)

    assert result["ok"] is True
    assert result["status"] == "ready"
    assert result["checks"]["http_reachable"] is True
    assert result["checks"]["http_status"] == 404
    assert "mcp_protocol_ready" not in result["checks"]
