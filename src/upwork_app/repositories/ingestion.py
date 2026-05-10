"""SQLite write helpers for normalized collector records."""

from __future__ import annotations

import sqlite3

from upwork_app.domain.collector_record import CollectorRecord


def insert_run(
    connection: sqlite3.Connection,
    *,
    run_id: str,
    source_query: str | None,
    input_path: str | None,
    started_at: str,
) -> None:
    connection.execute(
        """
        INSERT INTO ingest_runs (
          run_id, source_query, input_path, started_at, completed_at, record_count, status
        ) VALUES (?, ?, ?, ?, NULL, 0, 'running')
        """,
        (run_id, source_query, input_path, started_at),
    )


def complete_run(
    connection: sqlite3.Connection, *, run_id: str, completed_at: str, record_count: int
) -> None:
    connection.execute(
        """
        UPDATE ingest_runs
        SET completed_at = ?, record_count = ?, status = 'completed'
        WHERE run_id = ?
        """,
        (completed_at, record_count, run_id),
    )


def fail_run(connection: sqlite3.Connection, *, run_id: str, completed_at: str) -> None:
    connection.execute(
        """
        UPDATE ingest_runs
        SET completed_at = ?, status = 'failed'
        WHERE run_id = ?
        """,
        (completed_at, run_id),
    )


def upsert_job(connection: sqlite3.Connection, record: CollectorRecord, observed_at: str) -> None:
    connection.execute(
        """
        INSERT INTO jobs (
          job_id, source, title, description, url, posted_at, job_type, contractor_tier,
          hourly_min, hourly_max, fixed_amount, raw_id, content_hash, first_seen_at, last_seen_at
        ) VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
        ON CONFLICT(job_id) DO UPDATE SET
          source = excluded.source,
          title = excluded.title,
          description = excluded.description,
          url = excluded.url,
          posted_at = excluded.posted_at,
          job_type = excluded.job_type,
          contractor_tier = excluded.contractor_tier,
          hourly_min = excluded.hourly_min,
          hourly_max = excluded.hourly_max,
          fixed_amount = excluded.fixed_amount,
          raw_id = excluded.raw_id,
          content_hash = excluded.content_hash,
          last_seen_at = excluded.last_seen_at
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
            observed_at,
            observed_at,
        ),
    )


def replace_skills(connection: sqlite3.Connection, record: CollectorRecord) -> None:
    connection.execute("DELETE FROM job_skills WHERE job_id = ?", (record.job_id,))
    connection.executemany(
        "INSERT OR IGNORE INTO job_skills (job_id, skill) VALUES (?, ?)",
        [(record.job_id, skill) for skill in record.skills],
    )


def insert_observation(
    connection: sqlite3.Connection,
    *,
    record: CollectorRecord,
    run_id: str,
    source_query: str | None,
    observed_at: str,
    line_number: int,
) -> None:
    observation_id = f"{run_id}:{line_number}:{record.content_hash[:16]}"
    connection.execute(
        """
        INSERT OR IGNORE INTO job_observations (
          observation_id, job_id, run_id, source_query, observed_at, content_hash
        ) VALUES (?, ?, ?, ?, ?, ?)
        """,
        (observation_id, record.job_id, run_id, source_query, observed_at, record.content_hash),
    )


def insert_raw_record(
    connection: sqlite3.Connection,
    *,
    record: CollectorRecord,
    run_id: str,
    received_at: str,
    line_number: int,
) -> None:
    raw_record_id = f"{run_id}:{line_number}:raw:{record.content_hash[:16]}"
    connection.execute(
        """
        INSERT OR IGNORE INTO raw_records (
          raw_record_id, job_id, run_id, content_hash, received_at, payload_json
        ) VALUES (?, ?, ?, ?, ?, ?)
        """,
        (
            raw_record_id,
            record.job_id,
            run_id,
            record.content_hash,
            received_at,
            record.payload_json,
        ),
    )
