from __future__ import annotations

import argparse
from collections.abc import Sequence

from work_feed_mcp.cli import (
    analytics,
    collect,
    collect_scheduled,
    health,
    ingest,
    mcp_server,
    scheduler_status,
    worker,
)


def main(argv: Sequence[str] | None = None) -> int:
    args = list(argv) if argv is not None else None
    parser = argparse.ArgumentParser(prog="work-feed")
    subcommands = parser.add_subparsers(dest="command", required=True)
    subcommands.add_parser("collect", add_help=False)
    subcommands.add_parser("ingest", add_help=False)
    subcommands.add_parser("analytics", add_help=False)
    subcommands.add_parser("collect-scheduled", add_help=False)
    subcommands.add_parser("health", add_help=False)
    subcommands.add_parser("scheduler-status", add_help=False)
    subcommands.add_parser("worker", add_help=False)
    subcommands.add_parser("mcp-server", add_help=False)
    namespace, rest = parser.parse_known_args(args)
    command = namespace.command
    if command == "collect":
        return collect.main(rest)
    if command == "ingest":
        return ingest.main(rest)
    if command == "analytics":
        return analytics.main(rest)
    if command == "collect-scheduled":
        return collect_scheduled.main(rest)
    if command == "health":
        return health.main(rest)
    if command == "scheduler-status":
        return scheduler_status.main(rest)
    if command == "worker":
        return worker.main(rest)
    if command == "mcp-server":
        return mcp_server.main(rest)
    return 2


if __name__ == "__main__":
    raise SystemExit(main())
