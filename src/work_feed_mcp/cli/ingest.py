"""CLI for ingesting collector JSONL into SQLite."""

from __future__ import annotations

import argparse
import json
import sys
from collections.abc import Sequence
from dataclasses import asdict
from typing import Never

from work_feed_mcp.core.errors import IngestError, UsageError, exit_code_for_error
from work_feed_mcp.services.ingestion import ingest_jsonl


class IngestArgumentParser(argparse.ArgumentParser):
    def error(self, message: str) -> Never:
        raise UsageError(message)


def build_parser() -> argparse.ArgumentParser:
    parser = IngestArgumentParser(prog="work-feed ingest")
    parser.add_argument("--db", required=True)
    parser.add_argument("--input", required=True)
    parser.add_argument("--query", dest="source_query")
    return parser


def main(argv: Sequence[str] | None = None) -> int:
    try:
        args = build_parser().parse_args(argv)
        result = ingest_jsonl(
            db_path=args.db,
            input_path=args.input,
            source_query=args.source_query,
        )
        print(json.dumps(asdict(result), ensure_ascii=False, sort_keys=True))
        return 0
    except IngestError as exc:
        print(str(exc), file=sys.stderr)
        return exit_code_for_error(exc)


if __name__ == "__main__":
    raise SystemExit(main())
