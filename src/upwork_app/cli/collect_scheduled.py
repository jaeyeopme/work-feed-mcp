"""CLI for one-shot scheduled multi-query live collection."""

from __future__ import annotations

import argparse
import json
import sys
from collections.abc import Sequence
from typing import Never

from upwork_app.cli.args import add_live_paging_arguments
from upwork_app.core.errors import IngestError
from upwork_app.core.errors import exit_code_for_error as ingest_exit_code
from upwork_app.integrations.upwork.credentials import redact
from upwork_app.integrations.upwork.errors import (
    CollectorError,
    UsageError,
)
from upwork_app.integrations.upwork.errors import (
    exit_code_for_error as collector_exit_code,
)
from upwork_app.services.scheduled_collection import collect_scheduled, parse_queries


class ScheduledCollectionArgumentParser(argparse.ArgumentParser):
    def error(self, message: str) -> Never:
        raise UsageError(message)


def _queries(value: str) -> tuple[str, ...]:
    try:
        return parse_queries(value)
    except ValueError as exc:
        raise argparse.ArgumentTypeError(str(exc)) from exc


def build_parser() -> argparse.ArgumentParser:
    parser = ScheduledCollectionArgumentParser(prog="upwork-app collect-scheduled")
    parser.add_argument("--db", required=True)
    parser.add_argument("--queries", required=True, type=_queries)
    add_live_paging_arguments(parser)
    return parser


def main(argv: Sequence[str] | None = None) -> int:
    try:
        args = build_parser().parse_args(argv)
        result = collect_scheduled(
            db_path=args.db,
            queries=args.queries,
            max_pages=args.max_pages,
            page_size=args.page_size,
        )
        print(json.dumps(result.to_dict(), ensure_ascii=False, sort_keys=True))
        return 0
    except CollectorError as exc:
        print(redact(exc), file=sys.stderr)
        return collector_exit_code(exc)
    except IngestError as exc:
        print(redact(exc), file=sys.stderr)
        return ingest_exit_code(exc)


if __name__ == "__main__":
    raise SystemExit(main())
