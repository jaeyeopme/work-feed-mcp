"""CLI for agent-readable scheduled collector status."""

from __future__ import annotations

import argparse
import json
import sys
from collections.abc import Sequence
from pathlib import Path
from typing import Never

from work_feed_mcp.cli.args import bounded_positive_int
from work_feed_mcp.services.scheduler_status import SchedulerStatusError, scheduler_status


class SchedulerStatusArgumentParser(argparse.ArgumentParser):
    def error(self, message: str) -> Never:
        raise SchedulerStatusError(message)


def build_parser() -> argparse.ArgumentParser:
    parser = SchedulerStatusArgumentParser(prog="work-feed scheduler-status")
    parser.add_argument("--db", required=True)
    parser.add_argument(
        "--limit", type=lambda value: bounded_positive_int(value, maximum=100), default=5
    )
    return parser


def main(argv: Sequence[str] | None = None) -> int:
    try:
        args = build_parser().parse_args(argv)
        if not Path(args.db).exists():
            raise SchedulerStatusError("SQLite database path does not exist")
        result = scheduler_status(args.db, limit=args.limit)
        print(json.dumps(result, ensure_ascii=False, sort_keys=True))
        return 0
    except SchedulerStatusError as exc:
        print(str(exc), file=sys.stderr)
        return 2


if __name__ == "__main__":
    raise SystemExit(main())
