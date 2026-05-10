from __future__ import annotations

import argparse
from collections.abc import Sequence

from upwork_app.cli import analytics, collect, ingest


def main(argv: Sequence[str] | None = None) -> int:
    parser = argparse.ArgumentParser(prog="upwork-app")
    subcommands = parser.add_subparsers(dest="command", required=True)
    subcommands.add_parser("collect")
    subcommands.add_parser("ingest")
    subcommands.add_parser("analytics")
    known, rest = parser.parse_known_args(argv)
    if known.command == "collect":
        return collect.main(rest)
    if known.command == "ingest":
        return ingest.main(rest)
    if known.command == "analytics":
        return analytics.main(rest)
    return 2


if __name__ == "__main__":
    raise SystemExit(main())
