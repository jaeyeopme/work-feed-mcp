from __future__ import annotations

import json
import sqlite3

import pytest

from upwork_ingest.raw_records import (
    RawRecordValidationError,
    initialize_raw_record_schema,
    insert_raw_record,
)


def _collector_record() -> dict[str, object]:
    return {
        "source": "upwork",
        "id": "~02abc",
        "title": "Build a Python scraper",
        "description": "Need normalized JSON output.",
        "url": "https://www.upwork.com/jobs/~02abc",
        "skills": ["Python", "SQLite"],
        "posted_at": "2026-05-10T00:00:00Z",
        "job_type": "hourly",
        "contractor_tier": None,
        "hourly_min": 25.0,
        "hourly_max": 50.0,
        "fixed_amount": None,
        "raw_id": "raw-job-1",
    }


def test_raw_records_store_collector_emitted_normalized_json_only() -> None:
    conn = sqlite3.connect(":memory:")
    payload_json = json.dumps(_collector_record(), ensure_ascii=False, separators=(",", ":"))

    stored = insert_raw_record(
        conn,
        run_id="run-1",
        payload_json=payload_json,
        raw_record_id="raw-1",
        received_at="2026-05-10T00:00:00Z",
    )

    row = conn.execute(
        """
        SELECT raw_record_id, job_id, run_id, content_hash, received_at, payload_json
        FROM raw_records
        """
    ).fetchone()
    assert row == (
        "raw-1",
        "~02abc",
        "run-1",
        stored.content_hash,
        "2026-05-10T00:00:00Z",
        payload_json,
    )
    stored_payload = json.loads(row[5])
    assert set(stored_payload) == set(_collector_record())
    assert "job" not in stored_payload
    assert "data" not in stored_payload
    assert "errors" not in stored_payload
    assert "visitor_gql_token" not in stored_payload


def test_raw_records_reject_upstream_graphql_or_private_payloads() -> None:
    conn = sqlite3.connect(":memory:")
    initialize_raw_record_schema(conn)
    upstream_payload = json.dumps(
        {
            "data": {"search": {"results": []}},
            "errors": [],
            "visitor_gql_token": "secret-token",
        }
    )

    with pytest.raises(RawRecordValidationError, match="upstream/private"):
        insert_raw_record(conn, run_id="run-1", payload_json=upstream_payload)

    count = conn.execute("SELECT COUNT(*) FROM raw_records").fetchone()[0]
    assert count == 0


def test_raw_records_reject_non_contract_fields() -> None:
    conn = sqlite3.connect(":memory:")
    record = _collector_record()
    record["client_spend"] = 100000

    with pytest.raises(RawRecordValidationError, match="non-contract"):
        insert_raw_record(conn, run_id="run-1", payload_json=json.dumps(record))


def test_raw_record_content_hash_is_stable_for_equivalent_json_objects() -> None:
    conn = sqlite3.connect(":memory:")
    record = _collector_record()
    payload_a = json.dumps(record, sort_keys=True)
    payload_b = json.dumps(dict(reversed(list(record.items()))), sort_keys=False)

    first = insert_raw_record(conn, run_id="run-1", payload_json=payload_a, raw_record_id="raw-1")
    second = insert_raw_record(conn, run_id="run-1", payload_json=payload_b, raw_record_id="raw-2")

    assert first.content_hash == second.content_hash
    rows = conn.execute("SELECT payload_json FROM raw_records ORDER BY raw_record_id").fetchall()
    assert rows == [(payload_a,), (payload_b,)]
