"""OS scheduler control helpers for the Upwork collector timer."""

from __future__ import annotations

import subprocess
from collections.abc import Sequence
from dataclasses import dataclass
from typing import Any

DEFAULT_SERVICE_UNIT = "upwork-collector.service"
DEFAULT_TIMER_UNIT = "upwork-collector.timer"


@dataclass(frozen=True, slots=True)
class SchedulerCommandResult:
    action: str
    command: tuple[str, ...]
    returncode: int
    stdout: str
    stderr: str

    @property
    def ok(self) -> bool:
        return self.returncode == 0

    def to_dict(self) -> dict[str, Any]:
        return {
            "query": "scheduler-control",
            "action": self.action,
            "ok": self.ok,
            "returncode": self.returncode,
            "command": list(self.command),
            "stdout": self.stdout,
            "stderr": self.stderr,
        }


Runner = Any


def systemctl_command(*, user: bool, action: str, unit: str) -> tuple[str, ...]:
    command = ["systemctl"]
    if user:
        command.append("--user")
    command.extend([action, unit])
    if action == "status":
        command.append("--no-pager")
    return tuple(command)


def journalctl_command(*, user: bool, unit: str, lines: int) -> tuple[str, ...]:
    command = ["journalctl"]
    if user:
        command.append("--user")
    command.extend(["-u", unit, "--no-pager", "-n", str(lines)])
    return tuple(command)


def run_command(
    *,
    action: str,
    command: Sequence[str],
    runner: Runner = subprocess.run,
) -> SchedulerCommandResult:
    try:
        completed = runner(command, text=True, capture_output=True, check=False)
    except OSError as exc:
        return SchedulerCommandResult(
            action=action,
            command=tuple(command),
            returncode=127,
            stdout="",
            stderr=str(exc),
        )
    return SchedulerCommandResult(
        action=action,
        command=tuple(command),
        returncode=int(completed.returncode),
        stdout=str(completed.stdout),
        stderr=str(completed.stderr),
    )
