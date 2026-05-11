"""CLI for SQLite analytics queries."""

from __future__ import annotations

import argparse
import json
import sqlite3
import sys
from collections.abc import Sequence
from pathlib import Path
from typing import Never

from upwork_app.db.connection import connect_readonly
from upwork_app.services.analytics import run_query


class AnalyticsUsageError(Exception):
    pass


class AnalyticsArgumentParser(argparse.ArgumentParser):
    def error(self, message: str) -> Never:
        raise AnalyticsUsageError(message)


def build_parser() -> argparse.ArgumentParser:
    parser = AnalyticsArgumentParser(prog="upwork-app-analytics")
    parser.add_argument("name", choices=("summary", "skills", "jobs", "budgets", "clients"))
    parser.add_argument("--db", required=True)
    parser.add_argument("--skill")
    parser.add_argument("--title")
    return parser


def main(argv: Sequence[str] | None = None) -> int:
    try:
        args = build_parser().parse_args(argv)
        if not Path(args.db).exists():
            raise AnalyticsUsageError("SQLite database path does not exist")
        connection = connect_readonly(args.db)
        try:
            result = run_query(connection, args.name, skill=args.skill, title=args.title)
        finally:
            connection.close()
        print(json.dumps(result.to_dict(), ensure_ascii=False, sort_keys=True))
        return 0
    except AnalyticsUsageError as exc:
        print(str(exc), file=sys.stderr)
        return 2
    except sqlite3.Error as exc:
        print(f"sqlite failure: {exc}", file=sys.stderr)
        return 30


if __name__ == "__main__":
    raise SystemExit(main())
