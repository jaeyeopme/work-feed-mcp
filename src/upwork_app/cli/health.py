"""CLI healthcheck for Docker and local runtime diagnostics."""

from __future__ import annotations

import argparse
import json
from collections.abc import Sequence

from upwork_app.runtime.config import DEFAULT_DB_PATH
from upwork_app.services.health import health_check


def main(argv: Sequence[str] | None = None) -> int:
    parser = argparse.ArgumentParser(prog="upwork-app health")
    parser.add_argument("--db", default=DEFAULT_DB_PATH)
    parser.add_argument("--role", choices=["worker", "mcp", "all"], default="all")
    parser.add_argument("--http-url")
    parser.add_argument("--http-timeout", type=float, default=2.0)
    args = parser.parse_args(argv)

    result = health_check(
        args.db, role=args.role, http_url=args.http_url, http_timeout=args.http_timeout
    )
    print(json.dumps(result, sort_keys=True))
    return 0 if result["ok"] else 1
