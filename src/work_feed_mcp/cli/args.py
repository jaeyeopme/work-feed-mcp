"""Shared CLI argument validators."""

from __future__ import annotations

import argparse


def bounded_positive_int(value: str, *, maximum: int) -> int:
    try:
        parsed = int(value)
    except ValueError as exc:
        raise argparse.ArgumentTypeError("must be an integer") from exc
    if parsed < 1:
        raise argparse.ArgumentTypeError("must be >= 1")
    if parsed > maximum:
        raise argparse.ArgumentTypeError(f"must be <= {maximum}")
    return parsed


def add_live_paging_arguments(parser: argparse.ArgumentParser) -> None:
    """Add bounded live collection paging options."""

    parser.add_argument(
        "--max-pages", type=lambda value: bounded_positive_int(value, maximum=5), default=1
    )
    parser.add_argument(
        "--page-size", type=lambda value: bounded_positive_int(value, maximum=50), default=50
    )
