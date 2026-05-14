from __future__ import annotations

from pathlib import Path
from typing import Any

import pytest

from upwork_app.integrations.upwork.errors import UpstreamBlockedError
from upwork_app.integrations.upwork.models import Job
from upwork_app.services import scheduled_collection
from upwork_app.services.scheduled_collection import collect_scheduled, parse_queries


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
        db_path=str(tmp_path / "upwork.sqlite"),
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
    db = tmp_path / "upwork.sqlite"
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
