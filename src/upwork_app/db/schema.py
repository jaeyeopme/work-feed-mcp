"""SQLite schema for the jobs-only store."""

from __future__ import annotations

import sqlite3

SCHEMA_SQL = """
PRAGMA foreign_keys = ON;

CREATE TABLE IF NOT EXISTS jobs (
  job_id TEXT PRIMARY KEY,
  source TEXT NOT NULL,
  title TEXT NOT NULL,
  description TEXT NULL,
  url TEXT NULL,
  posted_at TEXT NULL,
  job_type TEXT NULL,
  contractor_tier TEXT NULL,
  hourly_min REAL NULL,
  hourly_max REAL NULL,
  fixed_amount REAL NULL,
  raw_id TEXT NULL,
  content_hash TEXT NOT NULL,
  first_seen_at TEXT NOT NULL,
  created_at TEXT NOT NULL
);

CREATE TABLE IF NOT EXISTS job_skills (
  job_id TEXT NOT NULL,
  skill TEXT NOT NULL,
  PRIMARY KEY (job_id, skill),
  FOREIGN KEY (job_id) REFERENCES jobs(job_id)
);

CREATE INDEX IF NOT EXISTS idx_jobs_content_hash ON jobs(content_hash);
CREATE INDEX IF NOT EXISTS idx_jobs_first_seen_at ON jobs(first_seen_at);
CREATE INDEX IF NOT EXISTS idx_job_skills_skill ON job_skills(skill);
"""


def initialize_schema(connection: sqlite3.Connection) -> None:
    connection.executescript(SCHEMA_SQL)
    connection.execute("PRAGMA foreign_keys = ON")
