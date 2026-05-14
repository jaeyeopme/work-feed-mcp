from __future__ import annotations

import json
from collections.abc import Sequence
from dataclasses import dataclass

import pytest

from upwork_app.cli import __main__, scheduler
from upwork_app.services import system_scheduler


@dataclass(frozen=True, slots=True)
class Completed:
    returncode: int = 0
    stdout: str = "ok"
    stderr: str = ""


def test_scheduler_restart_timer_wraps_user_systemctl(
    monkeypatch: pytest.MonkeyPatch, capsys: pytest.CaptureFixture[str]
) -> None:
    calls: list[tuple[str, ...]] = []

    def fake_run(command: Sequence[str], **kwargs: object) -> Completed:
        calls.append(tuple(command))
        assert kwargs["text"] is True
        assert kwargs["capture_output"] is True
        assert kwargs["check"] is False
        return Completed(stdout="restarted")

    monkeypatch.setattr(
        scheduler,
        "run_command",
        lambda **kwargs: system_scheduler.run_command(runner=fake_run, **kwargs),
    )

    assert scheduler.main(["restart-timer"]) == 0
    payload = json.loads(capsys.readouterr().out)

    assert calls == [("systemctl", "--user", "restart", "upwork-collector.timer")]
    assert payload["action"] == "restart-timer"
    assert payload["ok"] is True


def test_scheduler_run_now_starts_service_with_system_mode(
    monkeypatch: pytest.MonkeyPatch, capsys: pytest.CaptureFixture[str]
) -> None:
    calls: list[tuple[str, ...]] = []

    def fake_run(command: Sequence[str], **kwargs: object) -> Completed:
        calls.append(tuple(command))
        return Completed()

    monkeypatch.setattr(
        scheduler,
        "run_command",
        lambda **kwargs: system_scheduler.run_command(runner=fake_run, **kwargs),
    )

    assert scheduler.main(["run-now", "--system", "--service-unit", "custom.service"]) == 0
    payload = json.loads(capsys.readouterr().out)

    assert calls == [("systemctl", "start", "custom.service")]
    assert payload["command"] == ["systemctl", "start", "custom.service"]


def test_scheduler_logs_wraps_journalctl(
    monkeypatch: pytest.MonkeyPatch, capsys: pytest.CaptureFixture[str]
) -> None:
    calls: list[tuple[str, ...]] = []

    def fake_run(command: Sequence[str], **kwargs: object) -> Completed:
        calls.append(tuple(command))
        return Completed(stdout="logs")

    monkeypatch.setattr(
        scheduler,
        "run_command",
        lambda **kwargs: system_scheduler.run_command(runner=fake_run, **kwargs),
    )

    assert scheduler.main(["logs", "--lines", "25"]) == 0
    payload = json.loads(capsys.readouterr().out)

    assert calls == [
        ("journalctl", "--user", "-u", "upwork-collector.service", "--no-pager", "-n", "25")
    ]
    assert payload["stdout"] == "logs"


def test_top_level_cli_dispatches_scheduler(monkeypatch: pytest.MonkeyPatch) -> None:
    called: list[list[str]] = []

    def fake_main(argv: list[str]) -> int:
        called.append(argv)
        return 0

    monkeypatch.setattr(scheduler, "main", fake_main)

    assert __main__.main(["scheduler", "restart-timer"]) == 0
    assert called == [["restart-timer"]]


def test_scheduler_missing_systemctl_returns_json(
    monkeypatch: pytest.MonkeyPatch, capsys: pytest.CaptureFixture[str]
) -> None:
    def fake_run(command: Sequence[str], **kwargs: object) -> Completed:
        raise FileNotFoundError("systemctl missing")

    monkeypatch.setattr(
        scheduler,
        "run_command",
        lambda **kwargs: system_scheduler.run_command(runner=fake_run, **kwargs),
    )

    assert scheduler.main(["restart-timer"]) == 127
    payload = json.loads(capsys.readouterr().out)
    assert payload["ok"] is False
    assert payload["returncode"] == 127
    assert "systemctl missing" in payload["stderr"]
