"""Command-line interface for upwork-collector."""

from __future__ import annotations

import argparse
import json
import sys
from collections.abc import Sequence
from pathlib import Path
from typing import Never

from upwork_collector.credentials import redact
from upwork_collector.errors import CollectorError, ExitCode, UsageError, exit_code_for_error
from upwork_collector.normalize import normalize_response
from upwork_collector.transport import collect_live


def _bounded_positive_int(value: str, *, maximum: int) -> int:
    try:
        parsed = int(value)
    except ValueError as exc:
        raise argparse.ArgumentTypeError("must be an integer") from exc
    if parsed < 1:
        raise argparse.ArgumentTypeError("must be >= 1")
    if parsed > maximum:
        raise argparse.ArgumentTypeError(f"must be <= {maximum}")
    return parsed


def _max_pages(value: str) -> int:
    return _bounded_positive_int(value, maximum=5)


def _page_size(value: str) -> int:
    return _bounded_positive_int(value, maximum=50)


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
    collect.add_argument("--page-size", type=_page_size, default=10)
    collect.add_argument("--output", choices=["jsonl"], default="jsonl")

    live = subcommands.add_parser("live-smoke")
    live.add_argument("--query")
    live.add_argument("--max-pages", type=_max_pages, default=1)
    live.add_argument("--page-size", type=_page_size, default=10)
    return parser


def _load_fixture(path: Path) -> dict[str, object]:
    try:
        data = json.loads(path.read_text(encoding="utf-8"))
    except OSError as exc:
        raise UsageError("fixture path is missing or unreadable") from exc
    except json.JSONDecodeError as exc:
        raise UsageError("fixture must contain valid JSON") from exc
    if not isinstance(data, dict):
        raise UsageError("fixture must contain a JSON object")
    return data


def _emit_jobs_from_response(response: dict[str, object]) -> int:
    jobs = normalize_response(response)
    for job in jobs:
        print(json.dumps(job.to_dict(), ensure_ascii=False, separators=(",", ":")))
    return int(ExitCode.SUCCESS)


def _run_collect(args: argparse.Namespace) -> int:
    if args.fixture and args.live:
        raise UsageError("--fixture and --live are mutually exclusive")
    if not args.fixture and not args.live:
        raise UsageError("collect requires --fixture or --live")
    if args.fixture:
        return _emit_jobs_from_response(_load_fixture(args.fixture))

    responses = collect_live(args.query, max_pages=args.max_pages, page_size=args.page_size)
    emitted = 0
    for response in responses:
        jobs = normalize_response(response)
        for job in jobs:
            print(json.dumps(job.to_dict(), ensure_ascii=False, separators=(",", ":")))
            emitted += 1
    if emitted == 0:
        raise CollectorError(
            "live collection returned zero jobs", ExitCode.UPSTREAM_SCHEMA_OR_TEMPORARY_FAILURE
        )
    return int(ExitCode.SUCCESS)


def _run_live_smoke(args: argparse.Namespace) -> int:
    responses = collect_live(args.query, max_pages=args.max_pages, page_size=args.page_size)
    emitted = 0
    for response in responses:
        for job in normalize_response(response):
            print(json.dumps(job.to_dict(), ensure_ascii=False, separators=(",", ":")))
            emitted += 1
    if emitted == 0:
        raise CollectorError(
            "live smoke returned zero jobs", ExitCode.UPSTREAM_SCHEMA_OR_TEMPORARY_FAILURE
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
