"""SQLite write helpers for normalized collector records."""

from __future__ import annotations

import sqlite3

from work_feed_mcp.domain.collector_record import CollectorRecord


def insert_job_if_new(
    connection: sqlite3.Connection, record: CollectorRecord, first_seen_at: str
) -> bool:
    cursor = connection.execute(
        """
        INSERT OR IGNORE INTO jobs (
          job_id, source, title, description, url, posted_at, job_type, contractor_tier,
          hourly_min, hourly_max, fixed_amount, raw_id, content_hash, first_seen_at, created_at
        ) VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
        """,
        (
            record.job_id,
            record.source,
            record.title,
            record.description,
            record.url,
            record.posted_at,
            record.job_type,
            record.contractor_tier,
            record.hourly_min,
            record.hourly_max,
            record.fixed_amount,
            record.raw_id,
            record.content_hash,
            first_seen_at,
            first_seen_at,
        ),
    )
    return cursor.rowcount == 1


def insert_skills(connection: sqlite3.Connection, record: CollectorRecord) -> None:
    connection.executemany(
        "INSERT OR IGNORE INTO job_skills (job_id, skill) VALUES (?, ?)",
        [(record.job_id, skill) for skill in record.skills],
    )
