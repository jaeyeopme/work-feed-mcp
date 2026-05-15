from __future__ import annotations

import json
from pathlib import Path

from upwork_app.cli import __main__, health
from upwork_app.db.connection import connect_worker
from upwork_app.repositories import collector_control
from upwork_app.runtime.config import RuntimeSettings


def test_health_cli_ready(tmp_path: Path, capsys) -> None:  # type: ignore[no-untyped-def]
    db = tmp_path / "upwork.sqlite"
    with connect_worker(str(db)) as connection:
        collector_control.seed_config(
            connection, RuntimeSettings(db_path=str(db)).persisted_defaults()
        )
        connection.commit()

    assert health.main(["--db", str(db), "--role", "worker"]) == 0
    payload = json.loads(capsys.readouterr().out)
    assert payload["ok"] is True
    assert payload["role"] == "worker"


def test_top_level_cli_dispatches_health(monkeypatch) -> None:  # type: ignore[no-untyped-def]
    from upwork_app.cli import health as health_module

    calls: list[list[str]] = []

    def fake_main(argv: list[str]) -> int:
        calls.append(argv)
        return 0

    monkeypatch.setattr(health_module, "main", fake_main)
    assert __main__.main(["health", "--db", "x"]) == 0
    assert calls == [["--db", "x"]]
