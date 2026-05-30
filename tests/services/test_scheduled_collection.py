from __future__ import annotations

from pathlib import Path
from typing import Any

import pytest

from work_feed_mcp.integrations.upwork.errors import UpstreamBlockedError
from work_feed_mcp.integrations.upwork.models import Job
from work_feed_mcp.services import scheduled_collection
from work_feed_mcp.services.scheduled_collection import collect_scheduled, parse_queries


def _job(job_id: str, *, title: str = "Python scraper") -> Job:
    return Job(
        source="upwork",
        id=job_id,
        title=title,
        description="Build a scraper",
        url=f"https://www.upwork.com/jobs/{job_id}",
        skills=["Python", "Scraping"],
        job_type="hourly",
        hourly_min=30.0,
        hourly_max=50.0,
        raw_id=job_id.removeprefix("~"),
    )


def test_parse_queries_trims_and_drops_empty_entries() -> None:
    assert parse_queries(" python , scraping,automation , ") == (
        "python",
        "scraping",
        "automation",
    )
    assert parse_queries("python scraping,automation") == ("python scraping", "automation")


@pytest.mark.parametrize("value", ["", ",", " , , "])
def test_parse_queries_rejects_empty_query_sets(value: str) -> None:
    with pytest.raises(ValueError, match="at least one query"):
        parse_queries(value)


def test_collect_scheduled_collects_and_ingests_each_query(
    tmp_path: Path, monkeypatch: pytest.MonkeyPatch
) -> None:
    calls: list[str | None] = []

    def fake_collect_jobs(**kwargs: Any) -> list[Job]:
        calls.append(kwargs["query"])
        return [_job(f"~{len(calls)}")]

    monkeypatch.setattr(scheduled_collection, "collect_jobs", fake_collect_jobs)

    result = collect_scheduled(
        db_path=str(tmp_path / "work-feed.sqlite"),
        queries=("python", "scraping"),
        max_pages=1,
        page_size=50,
    )

    assert calls == ["python", "scraping"]
    assert result.query_count == 2
    assert [item.query for item in result.results] == ["python", "scraping"]
    assert [item.inserted_count for item in result.results] == [1, 1]
    assert result.results[0].seen_count == 1


def test_collect_scheduled_fails_fast_and_keeps_completed_ingest(
    tmp_path: Path, monkeypatch: pytest.MonkeyPatch
) -> None:
    db = tmp_path / "work-feed.sqlite"
    calls: list[str | None] = []

    def fake_collect_jobs(**kwargs: Any) -> list[Job]:
        query = kwargs["query"]
        calls.append(query)
        if query == "scraping":
            raise UpstreamBlockedError("blocked token=secret")
        return [_job("~first")]

    monkeypatch.setattr(scheduled_collection, "collect_jobs", fake_collect_jobs)

    with pytest.raises(UpstreamBlockedError):
        collect_scheduled(
            db_path=str(db),
            queries=("python", "scraping", "automation"),
            max_pages=1,
            page_size=50,
        )

    assert calls == ["python", "scraping"]

    import sqlite3

    connection = sqlite3.connect(db)
    try:
        assert connection.execute("SELECT COUNT(*) FROM jobs").fetchone()[0] == 1
    finally:
        connection.close()


def test_collect_scheduled_defaults_to_unfiltered_run_history(
    tmp_path: Path, monkeypatch: pytest.MonkeyPatch
) -> None:
    db = tmp_path / "work-feed.sqlite"
    calls: list[str | None] = []

    def fake_collect_jobs(**kwargs: Any) -> list[Job]:
        calls.append(kwargs["query"])
        return [_job("~default")]

    monkeypatch.setattr(scheduled_collection, "collect_jobs", fake_collect_jobs)

    result = collect_scheduled(
        db_path=str(db),
        queries=None,
        max_pages=5,
        page_size=50,
        run_id_factory=lambda: "run-default",
    )

    assert calls == [None]
    assert result.run_id == "run-default"
    assert result.query_count == 1
    assert result.results[0].query is None
    assert result.results[0].inserted_count == 1

    import sqlite3

    connection = sqlite3.connect(db)
    try:
        run = connection.execute(
            "SELECT status, query_count, total_seen, total_inserted FROM collector_runs"
        ).fetchone()
        assert run == ("success", 1, 1, 1)
        row = connection.execute(
            "SELECT query, status, attempts, seen_count, inserted_count FROM collector_run_results"
        ).fetchone()
        assert row == (None, "success", 1, 1, 1)
    finally:
        connection.close()


def test_collect_scheduled_records_retry_attempt_count(
    tmp_path: Path, monkeypatch: pytest.MonkeyPatch
) -> None:
    from work_feed_mcp.integrations.upwork.errors import UpstreamSchemaOrTemporaryError

    db = tmp_path / "work-feed.sqlite"
    calls = 0
    delays: list[float] = []

    def fake_collect_jobs(**kwargs: Any) -> list[Job]:
        nonlocal calls
        calls += 1
        if calls < 3:
            raise UpstreamSchemaOrTemporaryError("temporary")
        return [_job("~retry")]

    monkeypatch.setattr(scheduled_collection, "collect_jobs", fake_collect_jobs)

    result = collect_scheduled(
        db_path=str(db),
        queries=None,
        max_pages=5,
        page_size=50,
        sleep=delays.append,
        jitter=lambda low, high: low,
        run_id_factory=lambda: "run-retry",
    )

    assert result.results[0].attempts == 3
    assert delays == [24.0, 48.0]

    import sqlite3

    connection = sqlite3.connect(db)
    try:
        assert (
            connection.execute(
                "SELECT attempts FROM collector_run_results WHERE run_id = 'run-retry'"
            ).fetchone()[0]
            == 3
        )
    finally:
        connection.close()


def test_collect_scheduled_partial_failure_records_redacted_history(
    tmp_path: Path, monkeypatch: pytest.MonkeyPatch
) -> None:
    db = tmp_path / "work-feed.sqlite"

    def fake_collect_jobs(**kwargs: Any) -> list[Job]:
        if kwargs["query"] == "scraping":
            raise UpstreamBlockedError("blocked token=secret")
        return [_job("~first")]

    monkeypatch.setattr(scheduled_collection, "collect_jobs", fake_collect_jobs)

    with pytest.raises(UpstreamBlockedError):
        collect_scheduled(
            db_path=str(db),
            queries=("python", "scraping"),
            max_pages=1,
            page_size=50,
            run_id_factory=lambda: "run-fail",
        )

    import sqlite3

    connection = sqlite3.connect(db)
    try:
        run = connection.execute(
            "SELECT status, total_seen, total_inserted, error_type, redacted_error "
            "FROM collector_runs"
        ).fetchone()
        assert run[0:4] == ("failed", 1, 1, "UpstreamBlockedError")
        assert "token=<redacted>" in run[4]
        assert "secret" not in run[4]
        rows = connection.execute(
            "SELECT query, status, attempts, error_type, redacted_error "
            "FROM collector_run_results ORDER BY id"
        ).fetchall()
        assert rows[0] == ("python", "success", 1, None, None)
        assert rows[1][0:4] == ("scraping", "failed", 1, "UpstreamBlockedError")
        assert "token=<redacted>" in rows[1][4]
    finally:
        connection.close()


def test_collect_scheduled_records_ingest_failure_without_retry(
    tmp_path: Path, monkeypatch: pytest.MonkeyPatch
) -> None:
    from work_feed_mcp.core.errors import ValidationError

    db = tmp_path / "work-feed.sqlite"
    collect_calls: list[str | None] = []
    ingest_calls = 0
    real_ingest = scheduled_collection.ingest_records_into_connection

    def fake_collect_jobs(**kwargs: Any) -> list[Job]:
        collect_calls.append(kwargs["query"])
        return [_job(f"~{len(collect_calls)}")]

    def fake_ingest_records_into_connection(*args: Any, **kwargs: Any) -> Any:
        nonlocal ingest_calls
        ingest_calls += 1
        if ingest_calls == 2:
            raise ValidationError("invalid token=secret")
        return real_ingest(*args, **kwargs)

    monkeypatch.setattr(scheduled_collection, "collect_jobs", fake_collect_jobs)
    monkeypatch.setattr(
        scheduled_collection,
        "ingest_records_into_connection",
        fake_ingest_records_into_connection,
    )

    with pytest.raises(ValidationError) as exc_info:
        collect_scheduled(
            db_path=str(db),
            queries=("python", "scraping"),
            max_pages=1,
            page_size=50,
            run_id_factory=lambda: "run-ingest-fail",
        )

    assert collect_calls == ["python", "scraping"]
    assert ingest_calls == 2
    assert scheduled_collection.is_expected_operational_collection_failure(
        exc_info.value,
        db_path=str(db),
        trigger="scheduled",
    )
    assert not scheduled_collection.is_expected_operational_collection_failure(
        ValidationError("invalid token=secret"),
        db_path=str(tmp_path / "missing.sqlite"),
        trigger="scheduled",
    )

    import sqlite3

    connection = sqlite3.connect(db)
    try:
        run = connection.execute(
            "SELECT status, total_seen, total_inserted, error_type, redacted_error "
            "FROM collector_runs WHERE run_id = 'run-ingest-fail'"
        ).fetchone()
        assert run[0:4] == ("failed", 1, 1, "ValidationError")
        assert "token=<redacted>" in run[4]
        assert "secret" not in run[4]
        rows = connection.execute(
            "SELECT query, status, attempts, error_type, redacted_error "
            "FROM collector_run_results WHERE run_id = 'run-ingest-fail' ORDER BY id"
        ).fetchall()
        assert rows[0] == ("python", "success", 1, None, None)
        assert rows[1][0:4] == ("scraping", "failed", 1, "ValidationError")
        assert "token=<redacted>" in rows[1][4]
    finally:
        connection.close()
