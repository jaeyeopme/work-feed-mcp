"""Collection service that keeps Upwork transport details behind an integration boundary."""

from __future__ import annotations

import json
from pathlib import Path

from work_feed_mcp.integrations.upwork.errors import CollectorError, ExitCode, UsageError
from work_feed_mcp.integrations.upwork.models import Job
from work_feed_mcp.integrations.upwork.normalize import normalize_response
from work_feed_mcp.integrations.upwork.transport import collect_live


def load_fixture_response(path: str | Path) -> dict[str, object]:
    try:
        data = json.loads(Path(path).read_text(encoding="utf-8"))
    except OSError as exc:
        raise UsageError("fixture path is missing or unreadable") from exc
    except json.JSONDecodeError as exc:
        raise UsageError("fixture must contain valid JSON") from exc
    if not isinstance(data, dict):
        raise UsageError("fixture must contain a JSON object")
    return data


def collect_from_fixture(path: str | Path) -> list[Job]:
    return normalize_response(load_fixture_response(path))


def collect_jobs(
    *,
    fixture: str | None = None,
    live: bool = False,
    query: str | None = None,
    max_pages: int = 1,
    page_size: int = 50,
) -> list[Job]:
    if fixture and live:
        raise UsageError("fixture and live collection are mutually exclusive")
    if fixture:
        return collect_from_fixture(fixture)
    if not live:
        raise UsageError("collection requires fixture or live=true")

    jobs: list[Job] = []
    for response in collect_live(query, max_pages=max_pages, page_size=page_size):
        jobs.extend(normalize_response(response))
    if not jobs:
        raise CollectorError(
            "live collection returned zero jobs", ExitCode.UPSTREAM_SCHEMA_OR_TEMPORARY_FAILURE
        )
    return jobs


def jobs_to_jsonl(jobs: list[Job]) -> str:
    return "".join(
        json.dumps(job.to_dict(), ensure_ascii=False, separators=(",", ":")) + "\n" for job in jobs
    )
