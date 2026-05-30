from __future__ import annotations

from pathlib import Path
from typing import Any

from work_feed_mcp.db.connection import connect_worker
from work_feed_mcp.integrations.upwork.errors import UpstreamBlockedError
from work_feed_mcp.repositories import collector_control, run_history
from work_feed_mcp.runtime.config import RuntimeSettings, load_runtime_settings
from work_feed_mcp.runtime.worker import WorkerRuntime


class FakeResult:
    def __init__(self, trigger: str) -> None:
        self.trigger = trigger

    def to_dict(self) -> dict[str, Any]:
        return {"trigger": self.trigger}


def test_worker_invokes_collection_with_defaults(tmp_path: Path) -> None:
    calls: list[dict[str, Any]] = []

    def fake_collect_once(**kwargs: Any) -> FakeResult:
        calls.append(kwargs)
        return FakeResult(str(kwargs["trigger"]))

    settings = RuntimeSettings(db_path=str(tmp_path / "work-feed.sqlite"))
    runtime = WorkerRuntime(settings=settings, collect_once=fake_collect_once)
    runtime.run(max_iterations=1)

    assert calls == [
        {
            "db_path": settings.db_path,
            "queries": None,
            "max_pages": 5,
            "page_size": 50,
            "trigger": "worker_interval",
            "live": True,
            "fixture": None,
        }
    ]


def test_run_once_executes_while_paused(tmp_path: Path) -> None:
    calls: list[dict[str, Any]] = []

    def fake_collect_once(**kwargs: Any) -> FakeResult:
        calls.append(kwargs)
        return FakeResult(str(kwargs["trigger"]))

    settings = RuntimeSettings(db_path=str(tmp_path / "work-feed.sqlite"), paused=True)
    with connect_worker(settings.db_path) as connection:
        collector_control.seed_config(connection, settings.persisted_defaults())
        collector_control.enqueue_command(connection, "run_once", command_id="cmd-1")
        connection.commit()

    runtime = WorkerRuntime(settings=settings, collect_once=fake_collect_once)
    runtime.run(max_iterations=1)

    assert [call["trigger"] for call in calls] == ["mcp_run_once"]
    with connect_worker(settings.db_path) as connection:
        command = collector_control.command_status(connection, "cmd-1")
    assert command is not None
    assert command["status"] == "applied"


def test_failed_run_once_while_paused_marks_command_failed(tmp_path: Path) -> None:
    def fake_collect_once(**kwargs: Any) -> FakeResult:
        assert kwargs["trigger"] == "mcp_run_once"
        raise UpstreamBlockedError("blocked token=secret")

    settings = RuntimeSettings(db_path=str(tmp_path / "work-feed.sqlite"), paused=True)
    with connect_worker(settings.db_path) as connection:
        collector_control.seed_config(connection, settings.persisted_defaults())
        collector_control.enqueue_command(connection, "run_once", command_id="cmd-1")
        connection.commit()

    runtime = WorkerRuntime(settings=settings, collect_once=fake_collect_once)
    runtime.run(max_iterations=1)

    with connect_worker(settings.db_path) as connection:
        command = collector_control.command_status(connection, "cmd-1")
        config = collector_control.get_config(connection)
    assert command is not None
    assert command["status"] == "failed"
    assert command["error_type"] == "UpstreamBlockedError"
    assert "token=<redacted>" in str(command["redacted_error"])
    assert "secret" not in str(command["redacted_error"])
    assert config["paused"] is True


def test_pause_skips_scheduled_run(tmp_path: Path) -> None:
    calls: list[dict[str, Any]] = []
    settings = RuntimeSettings(db_path=str(tmp_path / "work-feed.sqlite"), paused=True)
    runtime = WorkerRuntime(settings=settings, collect_once=lambda **kwargs: calls.append(kwargs))
    runtime.run(max_iterations=1)
    assert calls == []


def test_collect_scheduled_accepts_trigger(tmp_path: Path) -> None:
    # Regression anchor for worker-triggered run history. Use direct run_history helper to
    # verify trigger vocabulary can be stored independently of worker wording.
    db = tmp_path / "work-feed.sqlite"
    with connect_worker(str(db)) as connection:
        run_history.create_run(
            connection,
            run_id="run-1",
            started_at="2026-05-15T00:00:00Z",
            trigger="mcp_run_once",
            query_count=1,
        )
        connection.commit()
        latest = run_history.latest_run(connection)
    assert latest is not None
    assert latest["trigger"] == "mcp_run_once"


def test_scheduled_collection_failure_does_not_stop_worker_and_later_command_runs(
    tmp_path: Path,
) -> None:
    def failing_collect_once(**kwargs: Any) -> FakeResult:
        with connect_worker(settings.db_path) as connection:
            started_at = "2026-05-30T00:00:00Z"
            run_history.create_run(
                connection,
                run_id="run-fail",
                started_at=started_at,
                trigger=str(kwargs["trigger"]),
                query_count=1,
            )
            run_history.insert_run_result(
                connection,
                run_id="run-fail",
                query="python",
                status="failed",
                attempts=1,
                seen_count=0,
                inserted_count=0,
                skipped_count=0,
                error_type="UpstreamBlockedError",
                redacted_error="blocked token=<redacted>",
                started_at=started_at,
                finished_at="2026-05-30T00:00:01Z",
            )
            run_history.finish_run_failure(
                connection,
                run_id="run-fail",
                finished_at="2026-05-30T00:00:01Z",
                totals=run_history.RunTotals(),
                error_type="UpstreamBlockedError",
                redacted_error="blocked token=<redacted>",
            )
            connection.commit()
        raise UpstreamBlockedError("blocked token=secret")

    settings = RuntimeSettings(db_path=str(tmp_path / "work-feed.sqlite"))
    runtime = WorkerRuntime(settings=settings, collect_once=failing_collect_once)
    result = runtime.run(max_iterations=1)
    assert result["ok"] is True

    with connect_worker(settings.db_path) as connection:
        latest = run_history.latest_run(connection)
        collector_control.enqueue_command(connection, "pause", command_id="cmd-pause")
        connection.commit()
    assert latest is not None
    assert latest["status"] == "failed"
    assert latest["error_type"] == "UpstreamBlockedError"

    runtime = WorkerRuntime(settings=settings, collect_once=failing_collect_once)
    runtime.run(max_iterations=1)

    with connect_worker(settings.db_path) as connection:
        command = collector_control.command_status(connection, "cmd-pause")
    assert command is not None
    assert command["status"] == "applied"


def test_scheduled_internal_programming_error_is_not_swallowed(tmp_path: Path) -> None:
    def broken_collect_once(**_kwargs: Any) -> FakeResult:
        raise RuntimeError("runtime bug token=secret")

    settings = RuntimeSettings(db_path=str(tmp_path / "work-feed.sqlite"))
    runtime = WorkerRuntime(settings=settings, collect_once=broken_collect_once)

    import pytest

    with pytest.raises(RuntimeError, match="runtime bug"):
        runtime.run(max_iterations=1)


def test_worker_stop_request_during_sleep_poll_exits_cleanly(tmp_path: Path) -> None:
    calls: list[float] = []
    settings = RuntimeSettings(db_path=str(tmp_path / "work-feed.sqlite"), paused=True)
    runtime = WorkerRuntime(settings=settings, collect_once=lambda **kwargs: None)

    def stop_during_sleep(seconds: float) -> None:
        calls.append(seconds)
        runtime.request_stop()

    runtime.sleep = stop_during_sleep
    result = runtime.run()

    assert result == {"ok": True, "iterations": 1, "stopped": True}
    assert calls == [5.0]


def test_worker_applies_update_config_command(tmp_path: Path) -> None:
    settings = RuntimeSettings(db_path=str(tmp_path / "work-feed.sqlite"), paused=True)
    with connect_worker(settings.db_path) as connection:
        collector_control.seed_config(connection, settings.persisted_defaults())
        collector_control.enqueue_command(
            connection,
            "update_config",
            payload={"updates": {"page_size": 25}},
            command_id="cmd-update",
        )
        connection.commit()

    runtime = WorkerRuntime(settings=settings, collect_once=lambda **kwargs: None)
    runtime.run(max_iterations=1)

    with connect_worker(settings.db_path) as connection:
        command = collector_control.command_status(connection, "cmd-update")
        config = collector_control.get_config(connection)
    assert command is not None
    assert command["status"] == "applied"
    assert config["page_size"] == 25


def test_worker_bootstraps_env_overrides_into_persisted_config(tmp_path: Path) -> None:
    db_path = str(tmp_path / "work-feed.sqlite")
    settings = load_runtime_settings(
        {
            "WORK_FEED_DB": db_path,
            "WORK_FEED_INTERVAL_SECONDS": "1800",
            "WORK_FEED_MAX_PAGES": "3",
            "WORK_FEED_PAGE_SIZE": "25",
            "WORK_FEED_QUERIES": "python,scraping",
            "WORK_FEED_PAUSED": "1",
        }
    )

    runtime = WorkerRuntime(settings=settings, collect_once=lambda **kwargs: None)
    runtime.run(max_iterations=1)

    with connect_worker(db_path) as connection:
        config = collector_control.get_config(connection)
    assert config == {
        "interval_seconds": 1800,
        "max_pages": 3,
        "page_size": 25,
        "paused": True,
        "queries": ["python", "scraping"],
    }
