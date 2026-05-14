from __future__ import annotations

import argparse
from collections.abc import Sequence

from upwork_app.cli import analytics, collect, collect_scheduled, ingest


def main(argv: Sequence[str] | None = None) -> int:
    parser = argparse.ArgumentParser(prog="upwork-app")
    subcommands = parser.add_subparsers(dest="command", required=True)
    subcommands.add_parser("collect")
    subcommands.add_parser("ingest")
    subcommands.add_parser("analytics")
    subcommands.add_parser("collect-scheduled")
    known, rest = parser.parse_known_args(argv)
    if known.command == "collect":
        return collect.main(rest)
    if known.command == "ingest":
        return ingest.main(rest)
    if known.command == "analytics":
        return analytics.main(rest)
    if known.command == "collect-scheduled":
        return collect_scheduled.main(rest)
    return 2


if __name__ == "__main__":
    raise SystemExit(main())
