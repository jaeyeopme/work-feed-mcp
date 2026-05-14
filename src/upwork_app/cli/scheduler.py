"""CLI wrapper around OS scheduler commands for the collector."""

from __future__ import annotations

import argparse
import json
import sys
from collections.abc import Sequence
from typing import Never

from upwork_app.cli.args import bounded_positive_int
from upwork_app.services.system_scheduler import (
    DEFAULT_SERVICE_UNIT,
    DEFAULT_TIMER_UNIT,
    journalctl_command,
    run_command,
    systemctl_command,
)


class SchedulerArgumentError(Exception):
    pass


class SchedulerArgumentParser(argparse.ArgumentParser):
    def error(self, message: str) -> Never:
        raise SchedulerArgumentError(message)


def _lines(value: str) -> int:
    return bounded_positive_int(value, maximum=1000)


def build_parser() -> argparse.ArgumentParser:
    parser = SchedulerArgumentParser(prog="upwork-app scheduler")
    parser.add_argument(
        "action",
        choices=(
            "timer-status",
            "start-timer",
            "restart-timer",
            "stop-timer",
            "enable-timer",
            "disable-timer",
            "run-now",
            "service-status",
            "logs",
        ),
    )
    parser.add_argument(
        "--system", action="store_true", help="Use system units instead of user units"
    )
    parser.add_argument("--timer-unit", default=DEFAULT_TIMER_UNIT)
    parser.add_argument("--service-unit", default=DEFAULT_SERVICE_UNIT)
    parser.add_argument("--lines", type=_lines, default=100)
    return parser


def _command_for(args: argparse.Namespace) -> tuple[str, ...]:
    user = not bool(args.system)
    action = str(args.action)
    timer_unit = str(args.timer_unit)
    service_unit = str(args.service_unit)
    if action == "timer-status":
        return systemctl_command(user=user, action="status", unit=timer_unit)
    if action == "start-timer":
        return systemctl_command(user=user, action="start", unit=timer_unit)
    if action == "restart-timer":
        return systemctl_command(user=user, action="restart", unit=timer_unit)
    if action == "stop-timer":
        return systemctl_command(user=user, action="stop", unit=timer_unit)
    if action == "enable-timer":
        return systemctl_command(user=user, action="enable", unit=timer_unit)
    if action == "disable-timer":
        return systemctl_command(user=user, action="disable", unit=timer_unit)
    if action == "run-now":
        return systemctl_command(user=user, action="start", unit=service_unit)
    if action == "service-status":
        return systemctl_command(user=user, action="status", unit=service_unit)
    if action == "logs":
        return journalctl_command(user=user, unit=service_unit, lines=int(args.lines))
    raise SchedulerArgumentError(f"unsupported action: {action}")


def main(argv: Sequence[str] | None = None) -> int:
    try:
        args = build_parser().parse_args(argv)
        command = _command_for(args)
        result = run_command(action=str(args.action), command=command)
        print(json.dumps(result.to_dict(), ensure_ascii=False, sort_keys=True))
        return result.returncode
    except SchedulerArgumentError as exc:
        print(str(exc), file=sys.stderr)
        return 2


if __name__ == "__main__":
    raise SystemExit(main())
