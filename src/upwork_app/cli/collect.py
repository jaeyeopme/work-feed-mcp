"""CLI for collecting normalized Upwork job records."""

from __future__ import annotations

import argparse
import sys
from collections.abc import Sequence
from typing import Never

from upwork_app.cli.args import add_live_paging_arguments
from upwork_app.cli.output import emit_jsonl
from upwork_app.integrations.upwork.credentials import redact
from upwork_app.integrations.upwork.errors import CollectorError, UsageError, exit_code_for_error
from upwork_app.services.collector import collect_jobs


class CollectorArgumentParser(argparse.ArgumentParser):
    def error(self, message: str) -> Never:
        raise UsageError(message)


def build_parser() -> argparse.ArgumentParser:
    parser = CollectorArgumentParser(prog="upwork-app-collect")
    parser.add_argument("--fixture")
    parser.add_argument("--live", action="store_true")
    parser.add_argument("--query")
    add_live_paging_arguments(parser)
    return parser


def main(argv: Sequence[str] | None = None) -> int:
    try:
        args = build_parser().parse_args(argv)
        emit_jsonl(
            collect_jobs(
                fixture=args.fixture,
                live=args.live,
                query=args.query,
                max_pages=args.max_pages,
                page_size=args.page_size,
            )
        )
        return 0
    except CollectorError as exc:
        print(redact(exc), file=sys.stderr)
        return exit_code_for_error(exc)


if __name__ == "__main__":
    raise SystemExit(main())
