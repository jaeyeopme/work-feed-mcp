from __future__ import annotations

import sqlite3
from pathlib import Path

from work_feed_mcp.db.connection import connect_worker
from work_feed_mcp.repositories import jobs


def _seed(connection: sqlite3.Connection) -> None:
    rows = [
        (
            "job-1",
            "upwork",
            "Python scraper",
            "desc",
            "https://example.com/1",
            None,
            "hourly",
            None,
            10,
            20,
            None,
            "raw-1",
            "hash-1",
            "2026-05-15T00:00:00Z",
            "2026-05-15T00:00:00Z",
        ),
        (
            "job-2",
            "upwork",
            "React app",
            None,
            "https://example.com/2",
            None,
            "fixed",
            None,
            None,
            None,
            100,
            "raw-2",
            "hash-2",
            "2026-05-14T00:00:00Z",
            "2026-05-14T00:00:00Z",
        ),
    ]
    connection.executemany(
        """
        INSERT INTO jobs (
          job_id, source, title, description, url, posted_at, job_type,
          contractor_tier, hourly_min, hourly_max, fixed_amount, raw_id,
          content_hash, first_seen_at, created_at
        ) VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
        """,
        rows,
    )
    connection.executemany(
        "INSERT INTO job_skills (job_id, skill) VALUES (?, ?)",
        [("job-1", "python"), ("job-1", "scraping"), ("job-2", "react")],
    )


def test_job_queries_return_detailed_json_safe_rows(tmp_path: Path) -> None:
    connection = connect_worker(str(tmp_path / "work-feed.sqlite"))
    try:
        _seed(connection)
        connection.commit()
        recent = jobs.recent_jobs(connection)
        search = jobs.search_jobs(connection, skill="python")
        detail = jobs.get_job(connection, "job-1")
    finally:
        connection.close()

    assert [row["job_id"] for row in recent] == ["job-1", "job-2"]
    assert [row["job_id"] for row in search] == ["job-1"]
    assert detail is not None
    assert detail["skills"] == ["python", "scraping"]
    assert "private" not in detail
