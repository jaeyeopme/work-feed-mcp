"""Command-line interface for upwork-ingest."""

from __future__ import annotations

import argparse
import json
import sys
from collections.abc import Sequence
from typing import Never

from upwork_ingest.errors import IngestError, UsageError, exit_code_for_error
from upwork_ingest.ingest import ingest_jsonl


class IngestArgumentParser(argparse.ArgumentParser):
    def error(self, message: str) -> Never:
        raise UsageError(message)


def build_parser() -> argparse.ArgumentParser:
    parser = IngestArgumentParser(prog="upwork-ingest")
    subcommands = parser.add_subparsers(
        dest="command", required=True, parser_class=IngestArgumentParser
    )
    ingest = subcommands.add_parser("ingest")
    ingest.add_argument("--db", required=True, help="SQLite database path to create or update")
    ingest.add_argument("--input", required=True, help="JSONL file path, or '-' for stdin")
    ingest.add_argument("--query", dest="source_query", help="source query metadata for this run")
    ingest.add_argument("--run-id", help="optional caller-provided run id")
    return parser


def run(argv: Sequence[str] | None = None) -> int:
    parser = build_parser()
    args = parser.parse_args(argv)
    if args.command != "ingest":
        raise UsageError("unknown command")
    result = ingest_jsonl(
        db_path=args.db,
        input_path=args.input,
        source_query=args.source_query,
        run_id=args.run_id,
    )
    print(
        json.dumps(
            {
                "run_id": result.run_id,
                "record_count": result.record_count,
                "db_path": result.db_path,
                "input_path": result.input_path,
                "source_query": result.source_query,
            },
            ensure_ascii=False,
            sort_keys=True,
        )
    )
    return 0


def main(argv: Sequence[str] | None = None) -> int:
    try:
        return run(argv)
    except IngestError as exc:
        print(str(exc), file=sys.stderr)
        return exit_code_for_error(exc)
    except Exception as exc:  # pragma: no cover - defensive CLI boundary
        print(f"internal failure: {exc}", file=sys.stderr)
        return 40


if __name__ == "__main__":  # pragma: no cover
    raise SystemExit(main())
