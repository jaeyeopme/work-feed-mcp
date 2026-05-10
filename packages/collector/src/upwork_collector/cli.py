"""Command-line interface for upwork-collector."""

from __future__ import annotations

import argparse
import sys
from collections.abc import Sequence
from pathlib import Path
from typing import Never

from upwork_app.cli.args import bounded_positive_int
from upwork_app.cli.output import emit_jsonl
from upwork_app.services.collector import collect_jobs, load_fixture_response

from upwork_collector.credentials import redact
from upwork_collector.errors import CollectorError, ExitCode, UsageError, exit_code_for_error
from upwork_collector.normalize import normalize_response


def _max_pages(value: str) -> int:
    return bounded_positive_int(value, maximum=5)


def _page_size(value: str) -> int:
    return bounded_positive_int(value, maximum=50)


class CollectorArgumentParser(argparse.ArgumentParser):
    def error(self, message: str) -> Never:
        raise UsageError(message)


def build_parser() -> argparse.ArgumentParser:
    parser = CollectorArgumentParser(prog="upwork-collector")
    subcommands = parser.add_subparsers(
        dest="command", required=True, parser_class=CollectorArgumentParser
    )

    collect = subcommands.add_parser("collect")
    collect.add_argument("--fixture", type=Path)
    collect.add_argument("--live", action="store_true")
    collect.add_argument("--query")
    collect.add_argument("--max-pages", type=_max_pages, default=1)
    collect.add_argument("--page-size", type=_page_size, default=50)
    collect.add_argument("--output", choices=["jsonl"], default="jsonl")

    live = subcommands.add_parser("live-smoke")
    live.add_argument("--query")
    live.add_argument("--max-pages", type=_max_pages, default=1)
    live.add_argument("--page-size", type=_page_size, default=50)
    return parser


def _load_fixture(path: Path) -> dict[str, object]:
    return load_fixture_response(path)


def _emit_jobs_from_response(response: dict[str, object]) -> int:
    emit_jsonl(normalize_response(response))
    return int(ExitCode.SUCCESS)


def _run_collect(args: argparse.Namespace) -> int:
    if args.fixture and args.live:
        raise UsageError("--fixture and --live are mutually exclusive")
    if not args.fixture and not args.live:
        raise UsageError("collect requires --fixture or --live")
    if args.fixture:
        return _emit_jobs_from_response(_load_fixture(args.fixture))

    emit_jsonl(
        collect_jobs(
            live=True, query=args.query, max_pages=args.max_pages, page_size=args.page_size
        )
    )
    return int(ExitCode.SUCCESS)


def _run_live_smoke(args: argparse.Namespace) -> int:
    emit_jsonl(
        collect_jobs(
            live=True, query=args.query, max_pages=args.max_pages, page_size=args.page_size
        )
    )
    return int(ExitCode.SUCCESS)


def run(argv: Sequence[str] | None = None) -> int:
    parser = build_parser()
    args = parser.parse_args(argv)
    if args.command == "collect":
        return _run_collect(args)
    if args.command == "live-smoke":
        return _run_live_smoke(args)
    raise UsageError("unknown command")


def main(argv: Sequence[str] | None = None) -> int:
    try:
        return run(argv)
    except CollectorError as exc:
        print(redact(exc), file=sys.stderr)
        return exit_code_for_error(exc)
    except Exception as exc:  # pragma: no cover - defensive CLI boundary
        print(redact(f"internal failure: {exc}"), file=sys.stderr)
        return int(ExitCode.INTERNAL_FAILURE)


if __name__ == "__main__":  # pragma: no cover
    raise SystemExit(main())
