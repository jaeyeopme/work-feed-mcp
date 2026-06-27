"""CLI for collecting normalized Upwork job records."""

from __future__ import annotations

import argparse
import json
import sys
from collections.abc import Sequence
from typing import Never

from work_feed_mcp.cli.args import add_live_paging_arguments
from work_feed_mcp.integrations.upwork.credentials import redact
from work_feed_mcp.integrations.upwork.errors import CollectorError, UsageError, exit_code_for_error
from work_feed_mcp.services.collector import collect_jobs


class CollectorArgumentParser(argparse.ArgumentParser):
    def error(self, message: str) -> Never:
        raise UsageError(message)


def build_parser() -> argparse.ArgumentParser:
    parser = CollectorArgumentParser(prog="work-feed collect")
    parser.add_argument("--fixture")
    parser.add_argument("--live", action="store_true")
    parser.add_argument("--query")
    add_live_paging_arguments(parser)
    return parser


def main(argv: Sequence[str] | None = None) -> int:
    try:
        args = build_parser().parse_args(argv)
        jobs = collect_jobs(
            fixture=args.fixture,
            live=args.live,
            query=args.query,
            max_pages=args.max_pages,
            page_size=args.page_size,
        )
        for job in jobs:
            print(json.dumps(job.to_dict(), ensure_ascii=False, separators=(",", ":")))
        return 0
    except CollectorError as exc:
        print(redact(exc), file=sys.stderr)
        return exit_code_for_error(exc)


if __name__ == "__main__":
    raise SystemExit(main())
