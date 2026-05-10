"""Compatibility shim for SQLite analytics queries."""

from upwork_app.repositories.analytics import (
    QueryResult,
    budgets,
    clients,
    jobs,
    runs,
    skills,
    summary,
)

__all__ = ["QueryResult", "budgets", "clients", "jobs", "runs", "skills", "summary"]
