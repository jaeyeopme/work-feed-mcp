"""SQLite schema for persisted collector records."""

from __future__ import annotations

import sqlite3

SCHEMA_SQL = """
PRAGMA foreign_keys = ON;

CREATE TABLE IF NOT EXISTS ingest_runs (
  run_id TEXT PRIMARY KEY,
  source_query TEXT NULL,
  input_path TEXT NULL,
  started_at TEXT NOT NULL,
  completed_at TEXT NULL,
  record_count INTEGER NOT NULL DEFAULT 0,
  status TEXT NOT NULL
);

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
  last_seen_at TEXT NOT NULL
);

CREATE TABLE IF NOT EXISTS job_skills (
  job_id TEXT NOT NULL,
  skill TEXT NOT NULL,
  PRIMARY KEY (job_id, skill),
  FOREIGN KEY (job_id) REFERENCES jobs(job_id)
);

CREATE TABLE IF NOT EXISTS job_observations (
  observation_id TEXT PRIMARY KEY,
  job_id TEXT NOT NULL,
  run_id TEXT NOT NULL,
  source_query TEXT NULL,
  observed_at TEXT NOT NULL,
  content_hash TEXT NOT NULL,
  FOREIGN KEY (job_id) REFERENCES jobs(job_id),
  FOREIGN KEY (run_id) REFERENCES ingest_runs(run_id)
);

CREATE TABLE IF NOT EXISTS raw_records (
  raw_record_id TEXT PRIMARY KEY,
  job_id TEXT NULL,
  run_id TEXT NOT NULL,
  content_hash TEXT NOT NULL,
  received_at TEXT NOT NULL,
  payload_json TEXT NOT NULL,
  FOREIGN KEY (run_id) REFERENCES ingest_runs(run_id)
);

CREATE INDEX IF NOT EXISTS idx_jobs_content_hash ON jobs(content_hash);
CREATE INDEX IF NOT EXISTS idx_job_skills_skill ON job_skills(skill);
CREATE INDEX IF NOT EXISTS idx_job_observations_run_id ON job_observations(run_id);
CREATE INDEX IF NOT EXISTS idx_job_observations_source_query ON job_observations(source_query);
CREATE INDEX IF NOT EXISTS idx_raw_records_content_hash ON raw_records(content_hash);
"""


def initialize_schema(connection: sqlite3.Connection) -> None:
    connection.executescript(SCHEMA_SQL)
    connection.execute("PRAGMA foreign_keys = ON")
