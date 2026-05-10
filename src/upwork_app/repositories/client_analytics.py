"""Conditional client analytics over the SQLite jobs table.

Client dimensions are only meaningful when an upstream collector contract and
an ingest schema have explicitly provided those fields. This module therefore
inspects the stored jobs schema before querying any client dimension and never
falls back to title/description inference.
"""

from __future__ import annotations

import sqlite3
from dataclasses import dataclass
from typing import Final

DEFAULT_CLIENT_DIMENSIONS: Final[tuple[str, ...]] = (
    "client_country",
    "client_timezone",
    "client_payment_verified",
    "client_tier",
)


@dataclass(frozen=True, slots=True)
class ClientDimensionBucket:
    """Count for one client-dimension bucket.

    `value` is `None` when the dimension itself is unavailable in the stored
    schema. Present dimensions use the literal stored value or `"unknown"` for
    row-level NULL/empty values.
    """

    value: str | None
    label: str
    count: int


@dataclass(frozen=True, slots=True)
class ClientDimension:
    """Conditional aggregation result for one client dimension."""

    name: str
    available: bool
    buckets: tuple[ClientDimensionBucket, ...]


def client_dimension_buckets(
    connection: sqlite3.Connection,
    dimensions: tuple[str, ...] = DEFAULT_CLIENT_DIMENSIONS,
) -> tuple[ClientDimension, ...]:
    """Return client-dimension buckets without fabricating absent fields.

    If a requested client dimension is absent from `jobs`, all jobs are grouped
    under an unavailable `unknown` bucket with `value=None`. If the column is
    present, actual stored values are grouped directly and row-level NULL/empty
    values are grouped under the literal `unknown` bucket.
    """

    job_columns = _table_columns(connection, "jobs")
    total_jobs = _total_jobs(connection)
    results: list[ClientDimension] = []

    for dimension in dimensions:
        if dimension not in job_columns:
            results.append(
                ClientDimension(
                    name=dimension,
                    available=False,
                    buckets=(ClientDimensionBucket(value=None, label="unknown", count=total_jobs),),
                )
            )
            continue

        buckets = tuple(
            ClientDimensionBucket(value=label, label=label, count=count)
            for label, count in _group_present_dimension(connection, dimension)
        )
        results.append(ClientDimension(name=dimension, available=True, buckets=buckets))

    return tuple(results)


def _table_columns(connection: sqlite3.Connection, table_name: str) -> set[str]:
    rows = connection.execute(f"PRAGMA table_info({_quote_identifier(table_name)})").fetchall()
    columns: set[str] = set()
    for row in rows:
        columns.add(str(row[1]))
    return columns


def _total_jobs(connection: sqlite3.Connection) -> int:
    row = connection.execute("SELECT COUNT(*) FROM jobs").fetchone()
    if row is None:
        return 0
    value = row[0]
    if not isinstance(value, int):
        return 0
    return value


def _group_present_dimension(
    connection: sqlite3.Connection, dimension: str
) -> list[tuple[str, int]]:
    quoted_dimension = _quote_identifier(dimension)
    rows = connection.execute(
        f"""
        SELECT COALESCE(NULLIF(TRIM(CAST({quoted_dimension} AS TEXT)), ''), 'unknown') AS bucket,
               COUNT(*) AS count
          FROM jobs
         GROUP BY bucket
         ORDER BY bucket
        """
    ).fetchall()

    buckets: list[tuple[str, int]] = []
    for row in rows:
        label = str(row[0])
        count = row[1]
        buckets.append((label, count if isinstance(count, int) else 0))
    return buckets


def _quote_identifier(identifier: str) -> str:
    if not identifier or any(
        character not in "_abcdefghijklmnopqrstuvwxyz0123456789" for character in identifier
    ):
        raise ValueError(f"unsupported identifier: {identifier}")
    return f'"{identifier}"'
