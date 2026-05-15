"""CLI entrypoint for the Docker collector worker."""

from __future__ import annotations

import argparse
import json
from collections.abc import Sequence

from work_feed_mcp.runtime.config import load_runtime_settings
from work_feed_mcp.runtime.worker import WorkerRuntime


def main(argv: Sequence[str] | None = None) -> int:
    parser = argparse.ArgumentParser(prog="work-feed worker")
    parser.add_argument("--max-iterations", type=int, default=None)
    args = parser.parse_args(argv)
    runtime = WorkerRuntime(load_runtime_settings())
    result = runtime.run(max_iterations=args.max_iterations)
    print(json.dumps(result, sort_keys=True))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
