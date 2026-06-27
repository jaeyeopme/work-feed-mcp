"""CLI for agent-readable scheduled collector status."""

from __future__ import annotations

import argparse
import json
import sqlite3
import sys
from collections.abc import Sequence
from typing import Never

from work_feed_mcp.cli.args import bounded_positive_int
from work_feed_mcp.services.collector_control import NotReadyError
from work_feed_mcp.services.run_status import run_status


class SchedulerStatusUsageError(Exception):
    pass


class SchedulerStatusArgumentParser(argparse.ArgumentParser):
    def error(self, message: str) -> Never:
        raise SchedulerStatusUsageError(message)


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
        result = {"query": "scheduler-status", **run_status(args.db, limit=args.limit)}
        print(json.dumps(result, ensure_ascii=False, sort_keys=True))
        return 0
    except NotReadyError as exc:
        print(json.dumps(exc.to_dict(), ensure_ascii=False, sort_keys=True))
        return 2
    except SchedulerStatusUsageError as exc:
        print(str(exc), file=sys.stderr)
        return 2
    except sqlite3.Error as exc:
        print(f"scheduler status query failed: {exc}", file=sys.stderr)
        return 2


if __name__ == "__main__":
    raise SystemExit(main())
