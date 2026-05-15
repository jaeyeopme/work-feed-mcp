"""CLI entrypoint for the work-feed MCP server."""

from __future__ import annotations

import argparse
from collections.abc import Sequence

from work_feed_mcp.mcp_server.server import run_server
from work_feed_mcp.runtime.config import load_runtime_settings


def main(argv: Sequence[str] | None = None) -> int:
    parser = argparse.ArgumentParser(prog="work-feed mcp-server")
    parser.parse_args(argv)
    run_server(load_runtime_settings())
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
