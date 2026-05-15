from __future__ import annotations

from pathlib import Path

from work_feed_mcp.db.connection import connect_worker
from work_feed_mcp.repositories import collector_control
from work_feed_mcp.runtime.config import RuntimeSettings


def create_ready_runtime_db(db: Path) -> None:
    with connect_worker(str(db)) as connection:
        collector_control.seed_config(
            connection, RuntimeSettings(db_path=str(db)).persisted_defaults()
        )
        connection.commit()
