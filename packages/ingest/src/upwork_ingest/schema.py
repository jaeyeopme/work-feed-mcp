"""Compatibility shim for SQLite schema setup."""

from upwork_app.db.schema import SCHEMA_SQL, initialize_schema

__all__ = ["SCHEMA_SQL", "initialize_schema"]
