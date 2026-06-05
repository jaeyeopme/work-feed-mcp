from __future__ import annotations

import json
from pathlib import Path
from typing import Any

import pytest
from tests.conftest import load_fixture

from work_feed_mcp.integrations.upwork.errors import CollectorError, ExitCode, UsageError
from work_feed_mcp.integrations.upwork.models import Job
from work_feed_mcp.services import collector


def _response_with_results(results: list[dict[str, Any]]) -> dict[str, Any]:
    return {
        "data": {
            "search": {
                "universalSearchNuxt": {
                    "visitorJobSearchV1": {
                        "results": results,
                    }
                }
            }
        }
    }


def _job(
    *,
    job_id: str = "cipher-job",
    title: str = "Job Title",
    skills: list[str] | None = None,
) -> Job:
    return Job(
        source="upwork",
        id=job_id,
        title=title,
        description="Description",
        url=f"https://www.upwork.com/jobs/{job_id}",
        skills=["Python"] if skills is None else skills,
        raw_id="raw-job",
    )


def test_load_fixture_response_rejects_missing_file(tmp_path: Path) -> None:
    with pytest.raises(UsageError, match="missing or unreadable"):
        collector.load_fixture_response(tmp_path / "missing.json")


def test_load_fixture_response_rejects_invalid_json(tmp_path: Path) -> None:
    fixture = tmp_path / "invalid.json"
    fixture.write_text("{", encoding="utf-8")

    with pytest.raises(UsageError, match="valid JSON"):
        collector.load_fixture_response(fixture)


def test_load_fixture_response_rejects_non_object_json(tmp_path: Path) -> None:
    fixture = tmp_path / "array.json"
    fixture.write_text("[]", encoding="utf-8")

    with pytest.raises(UsageError, match="JSON object"):
        collector.load_fixture_response(fixture)


def test_collect_jobs_rejects_fixture_and_live() -> None:
    with pytest.raises(UsageError, match="mutually exclusive"):
        collector.collect_jobs(fixture="fixture.json", live=True)


def test_collect_jobs_requires_fixture_or_live() -> None:
    with pytest.raises(UsageError, match="fixture or live=true"):
        collector.collect_jobs()


def test_collect_jobs_reads_fixture_response() -> None:
    jobs = collector.collect_jobs(fixture="tests/fixtures/visitor_job_search_response.json")

    assert len(jobs) == 2
    assert jobs[0].id == "cipher-job-1"
    assert jobs[0].skills == ["Python", "Data Scraping"]


def test_collect_jobs_flattens_live_pages(monkeypatch: pytest.MonkeyPatch) -> None:
    fixture = load_fixture("visitor_job_search_response.json")
    first_result = fixture["data"]["search"]["universalSearchNuxt"]["visitorJobSearchV1"][
        "results"
    ][0]
    second_result = fixture["data"]["search"]["universalSearchNuxt"]["visitorJobSearchV1"][
        "results"
    ][1]
    calls: list[dict[str, object]] = []

    def fake_collect_live(
        query: str | None, *, max_pages: int, page_size: int
    ) -> list[dict[str, Any]]:
        calls.append({"query": query, "max_pages": max_pages, "page_size": page_size})
        return [_response_with_results([first_result]), _response_with_results([second_result])]

    monkeypatch.setattr(collector, "collect_live", fake_collect_live)

    jobs = collector.collect_jobs(live=True, query="python", max_pages=2, page_size=25)

    assert calls == [{"query": "python", "max_pages": 2, "page_size": 25}]
    assert [job.id for job in jobs] == ["cipher-job-1", "cipher-job-2"]


def test_collect_jobs_fails_when_live_pages_have_zero_jobs(
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    def fake_collect_live(
        query: str | None, *, max_pages: int, page_size: int
    ) -> list[dict[str, Any]]:
        return [_response_with_results([])]

    monkeypatch.setattr(collector, "collect_live", fake_collect_live)

    with pytest.raises(CollectorError, match="zero jobs") as raised:
        collector.collect_jobs(live=True)

    assert raised.value.code == ExitCode.UPSTREAM_SCHEMA_OR_TEMPORARY_FAILURE


def test_jobs_to_jsonl_outputs_one_utf8_json_object_per_line() -> None:
    unicode_title = "Cafe " + chr(233)
    jsonl = collector.jobs_to_jsonl(
        [
            _job(job_id="cipher-1", title=unicode_title, skills=["Python"]),
            _job(job_id="cipher-2", title="Second", skills=["API"]),
        ]
    )

    lines = jsonl.splitlines()
    assert jsonl.endswith("\n")
    assert len(lines) == 2
    assert unicode_title in jsonl
    assert [json.loads(line)["id"] for line in lines] == ["cipher-1", "cipher-2"]
