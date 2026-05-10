"""Command-line interface for upwork-analytics."""

from __future__ import annotations

import argparse
import json
import sqlite3
import sys
from collections.abc import Sequence
from pathlib import Path
from typing import Never

from upwork_analytics import queries


class AnalyticsUsageError(Exception):
    """Raised for invalid command usage."""


class AnalyticsArgumentParser(argparse.ArgumentParser):
    def error(self, message: str) -> Never:
        raise AnalyticsUsageError(message)


def build_parser() -> argparse.ArgumentParser:
    parser = AnalyticsArgumentParser(prog="upwork-analytics")
    subcommands = parser.add_subparsers(
        dest="command", required=True, parser_class=AnalyticsArgumentParser
    )
    query = subcommands.add_parser("query")
    query.add_argument("name", choices=("summary", "skills", "jobs", "budgets", "runs", "clients"))
    query.add_argument("--db", required=True, help="SQLite database path to read")
    query.add_argument("--skill", help="job skill filter for query jobs")
    query.add_argument("--title", help="title keyword filter for query jobs")
    return parser


def run(argv: Sequence[str] | None = None) -> int:
    parser = build_parser()
    args = parser.parse_args(argv)
    if args.command != "query":
        raise AnalyticsUsageError("unknown command")
    db_path = Path(args.db)
    if not db_path.exists():
        raise AnalyticsUsageError("SQLite database path does not exist")

    connection = sqlite3.connect(f"file:{db_path}?mode=ro", uri=True)
    connection.row_factory = sqlite3.Row
    try:
        result = _run_query(connection, args)
    finally:
        connection.close()
    print(json.dumps(result.to_dict(), ensure_ascii=False, sort_keys=True))
    return 0


def _run_query(connection: sqlite3.Connection, args: argparse.Namespace) -> queries.QueryResult:
    match args.name:
        case "summary":
            return queries.summary(connection)
        case "skills":
            return queries.skills(connection)
        case "jobs":
            return queries.jobs(connection, skill=args.skill, title=args.title)
        case "budgets":
            return queries.budgets(connection)
        case "runs":
            return queries.runs(connection)
        case "clients":
            return queries.clients(connection)
    raise AnalyticsUsageError("unknown query")


def main(argv: Sequence[str] | None = None) -> int:
    try:
        return run(argv)
    except AnalyticsUsageError as exc:
        print(str(exc), file=sys.stderr)
        return 2
    except sqlite3.Error as exc:
        print(f"sqlite failure: {exc}", file=sys.stderr)
        return 30
    except Exception as exc:  # pragma: no cover - defensive CLI boundary
        print(f"internal failure: {exc}", file=sys.stderr)
        return 40


if __name__ == "__main__":  # pragma: no cover
    raise SystemExit(main())
