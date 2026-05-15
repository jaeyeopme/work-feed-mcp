"""SQLite schema for the jobs and collector operation store."""

from __future__ import annotations

import sqlite3
from dataclasses import dataclass

SCHEMA_VERSION = 1


@dataclass(frozen=True, slots=True)
class UnsupportedSchemaVersionError(Exception):
    found: int
    supported: int = SCHEMA_VERSION

    def __str__(self) -> str:
        return f"unsupported schema version: found {self.found}, supported <= {self.supported}"


def schema_version(connection: sqlite3.Connection) -> int:
    row = connection.execute("PRAGMA user_version").fetchone()
    return int(row[0]) if row is not None else 0


def assert_supported_schema_version(connection: sqlite3.Connection) -> int:
    version = schema_version(connection)
    if version > SCHEMA_VERSION:
        raise UnsupportedSchemaVersionError(version)
    return version


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

CREATE TABLE IF NOT EXISTS collector_runs (
  run_id TEXT PRIMARY KEY,
  started_at TEXT NOT NULL,
  finished_at TEXT NULL,
  status TEXT NOT NULL,
  trigger TEXT NOT NULL DEFAULT 'scheduled',
  query_count INTEGER NOT NULL DEFAULT 0,
  total_seen INTEGER NOT NULL DEFAULT 0,
  total_inserted INTEGER NOT NULL DEFAULT 0,
  total_skipped INTEGER NOT NULL DEFAULT 0,
  error_type TEXT NULL,
  redacted_error TEXT NULL,
  created_at TEXT NOT NULL
);

CREATE TABLE IF NOT EXISTS collector_run_results (
  id INTEGER PRIMARY KEY AUTOINCREMENT,
  run_id TEXT NOT NULL,
  query TEXT NULL,
  status TEXT NOT NULL,
  attempts INTEGER NOT NULL DEFAULT 1,
  seen_count INTEGER NOT NULL DEFAULT 0,
  inserted_count INTEGER NOT NULL DEFAULT 0,
  skipped_count INTEGER NOT NULL DEFAULT 0,
  error_type TEXT NULL,
  redacted_error TEXT NULL,
  started_at TEXT NOT NULL,
  finished_at TEXT NOT NULL,
  FOREIGN KEY (run_id) REFERENCES collector_runs(run_id)
);

CREATE INDEX IF NOT EXISTS idx_jobs_content_hash ON jobs(content_hash);
CREATE INDEX IF NOT EXISTS idx_jobs_first_seen_at ON jobs(first_seen_at);
CREATE INDEX IF NOT EXISTS idx_job_skills_skill ON job_skills(skill);
CREATE INDEX IF NOT EXISTS idx_collector_runs_started_at ON collector_runs(started_at);
CREATE INDEX IF NOT EXISTS idx_collector_run_results_run_id ON collector_run_results(run_id);
CREATE INDEX IF NOT EXISTS idx_collector_run_results_query ON collector_run_results(query);


CREATE TABLE IF NOT EXISTS collector_config (
  key TEXT PRIMARY KEY,
  value_json TEXT NOT NULL,
  updated_at TEXT NOT NULL,
  updated_by TEXT NOT NULL DEFAULT 'worker'
);

CREATE TABLE IF NOT EXISTS collector_commands (
  command_id TEXT PRIMARY KEY,
  command_type TEXT NOT NULL CHECK (
    command_type IN ('run_once', 'pause', 'resume', 'update_config')
  ),
  payload_json TEXT NOT NULL DEFAULT '{}',
  status TEXT NOT NULL CHECK (
    status IN ('queued', 'running', 'applied', 'failed')
  ),
  created_at TEXT NOT NULL,
  started_at TEXT NULL,
  finished_at TEXT NULL,
  requested_by TEXT NOT NULL DEFAULT 'mcp',
  result_json TEXT NULL,
  error_type TEXT NULL,
  redacted_error TEXT NULL
);

CREATE INDEX IF NOT EXISTS idx_collector_commands_status_created_at
  ON collector_commands(status, created_at);
CREATE INDEX IF NOT EXISTS idx_collector_commands_created_at
  ON collector_commands(created_at);
"""


def initialize_schema(connection: sqlite3.Connection) -> None:
    current_version = assert_supported_schema_version(connection)
    connection.executescript(SCHEMA_SQL)
    connection.execute("PRAGMA foreign_keys = ON")
    if current_version < SCHEMA_VERSION:
        connection.execute(f"PRAGMA user_version = {SCHEMA_VERSION}")
