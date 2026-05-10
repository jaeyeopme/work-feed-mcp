from __future__ import annotations

import sqlite3

from upwork_analytics.client import client_dimension_buckets


def test_missing_client_dimensions_return_unknown_without_inference() -> None:
    connection = sqlite3.connect(":memory:")
    connection.execute(
        """
        CREATE TABLE jobs (
            job_id TEXT PRIMARY KEY,
            title TEXT NOT NULL,
            description TEXT NULL
        )
        """
    )
    connection.executemany(
        "INSERT INTO jobs (job_id, title, description) VALUES (?, ?, ?)",
        [
            ("job-1", "US fintech client with verified payment", "Spent over 10k before"),
            ("job-2", "Germany timezone preference", "Looks like a rich client"),
        ],
    )

    dimensions = client_dimension_buckets(
        connection, dimensions=("client_country", "client_payment_verified")
    )

    assert [dimension.name for dimension in dimensions] == [
        "client_country",
        "client_payment_verified",
    ]
    for dimension in dimensions:
        assert dimension.available is False
        assert [(bucket.value, bucket.label, bucket.count) for bucket in dimension.buckets] == [
            (None, "unknown", 2)
        ]


def test_present_client_dimensions_group_values_and_row_level_unknowns() -> None:
    connection = sqlite3.connect(":memory:")
    connection.execute(
        """
        CREATE TABLE jobs (
            job_id TEXT PRIMARY KEY,
            title TEXT NOT NULL,
            description TEXT NULL,
            client_country TEXT NULL,
            client_payment_verified TEXT NULL
        )
        """
    )
    connection.executemany(
        """
        INSERT INTO jobs (
            job_id,
            title,
            description,
            client_country,
            client_payment_verified
        ) VALUES (?, ?, ?, ?, ?)
        """,
        [
            ("job-1", "Python API", "Build an API", "US", "true"),
            ("job-2", "Data scraper", "Scrape public data", None, "false"),
            ("job-3", "Backend", "Client says Canada in text", "", None),
        ],
    )

    dimensions = client_dimension_buckets(
        connection,
        dimensions=("client_country", "client_payment_verified", "client_timezone"),
    )

    by_name = {dimension.name: dimension for dimension in dimensions}
    assert by_name["client_country"].available is True
    assert [
        (bucket.value, bucket.label, bucket.count) for bucket in by_name["client_country"].buckets
    ] == [
        ("US", "US", 1),
        ("unknown", "unknown", 2),
    ]
    assert by_name["client_payment_verified"].available is True
    assert [
        (bucket.value, bucket.label, bucket.count)
        for bucket in by_name["client_payment_verified"].buckets
    ] == [
        ("false", "false", 1),
        ("true", "true", 1),
        ("unknown", "unknown", 1),
    ]
    assert by_name["client_timezone"].available is False
    assert [
        (bucket.value, bucket.label, bucket.count) for bucket in by_name["client_timezone"].buckets
    ] == [(None, "unknown", 3)]
