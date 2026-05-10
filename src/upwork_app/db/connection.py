"""SQLite connection helpers."""

from __future__ import annotations

import sqlite3
from pathlib import Path


def connect_readonly(db_path: str) -> sqlite3.Connection:
    path = Path(db_path)
    connection = sqlite3.connect(f"file:{path}?mode=ro", uri=True)
    connection.row_factory = sqlite3.Row
    return connection
