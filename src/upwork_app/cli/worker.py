"""CLI entrypoint for the Docker collector worker."""

from __future__ import annotations

import argparse
import json
from collections.abc import Sequence

from upwork_app.runtime.config import load_runtime_settings
from upwork_app.runtime.worker import WorkerRuntime


def main(argv: Sequence[str] | None = None) -> int:
    parser = argparse.ArgumentParser(prog="upwork-app worker")
    parser.add_argument("--max-iterations", type=int, default=None)
    args = parser.parse_args(argv)
    runtime = WorkerRuntime(load_runtime_settings())
    result = runtime.run(max_iterations=args.max_iterations)
    print(json.dumps(result, sort_keys=True))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
