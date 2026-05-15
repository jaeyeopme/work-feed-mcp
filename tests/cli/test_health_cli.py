from __future__ import annotations

import json
from pathlib import Path

from tests.collector_db_helpers import create_ready_runtime_db
from tests.http_helpers import reachable_http_url

from upwork_app.cli import __main__, health


def test_health_cli_ready(tmp_path: Path, capsys) -> None:  # type: ignore[no-untyped-def]
    db = tmp_path / "upwork.sqlite"
    create_ready_runtime_db(db)

    assert health.main(["--db", str(db), "--role", "worker"]) == 0
    payload = json.loads(capsys.readouterr().out)
    assert payload["ok"] is True
    assert payload["role"] == "worker"


def test_health_cli_mcp_unreachable_http(tmp_path: Path, capsys) -> None:  # type: ignore[no-untyped-def]
    db = tmp_path / "upwork.sqlite"
    create_ready_runtime_db(db)

    exit_code = health.main(
        [
            "--db",
            str(db),
            "--role",
            "mcp",
            "--http-url",
            "http://127.0.0.1:9/mcp",
            "--http-timeout",
            "0.2",
        ]
    )
    payload = json.loads(capsys.readouterr().out)

    assert exit_code == 1
    assert payload["ok"] is False
    assert payload["checks"]["http_reachable"] is False
    assert "http_error" in payload["checks"]


def test_health_cli_mcp_reachable_http(tmp_path: Path, capsys) -> None:  # type: ignore[no-untyped-def]
    db = tmp_path / "upwork.sqlite"
    create_ready_runtime_db(db)

    with reachable_http_url() as url:
        exit_code = health.main(
            [
                "--db",
                str(db),
                "--role",
                "mcp",
                "--http-url",
                url,
            ]
        )
    payload = json.loads(capsys.readouterr().out)

    assert exit_code == 0
    assert payload["checks"]["http_reachable"] is True


def test_top_level_cli_dispatches_health(monkeypatch) -> None:  # type: ignore[no-untyped-def]
    from upwork_app.cli import health as health_module

    calls: list[list[str]] = []

    def fake_main(argv: list[str]) -> int:
        calls.append(argv)
        return 0

    monkeypatch.setattr(health_module, "main", fake_main)
    assert __main__.main(["health", "--db", "x"]) == 0
    assert calls == [["--db", "x"]]
