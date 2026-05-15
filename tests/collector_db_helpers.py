from __future__ import annotations

from pathlib import Path

from upwork_app.db.connection import connect_worker
from upwork_app.repositories import collector_control
from upwork_app.runtime.config import RuntimeSettings


def create_ready_runtime_db(db: Path) -> None:
    with connect_worker(str(db)) as connection:
        collector_control.seed_config(
            connection, RuntimeSettings(db_path=str(db)).persisted_defaults()
        )
        connection.commit()
