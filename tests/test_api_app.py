from __future__ import annotations

import json
import sqlite3
from pathlib import Path

import pytest
from fastapi.testclient import TestClient

from upwork_app.main import app
from upwork_app.services.collector import jobs_to_jsonl
from upwork_app.services.ingestion import ingest_records, read_jsonl

FIXTURE = Path(__file__).parent / "fixtures" / "visitor_job_search_response.json"


def assert_two_jobs_persisted(db: Path) -> None:
    connection = sqlite3.connect(db)
    try:
        assert connection.execute("SELECT COUNT(*) FROM jobs").fetchone()[0] == 2
    finally:
        connection.close()


def assert_inserted_two_jobs_response(response) -> None:  # type: ignore[no-untyped-def]
    assert response.status_code == 200
    assert response.json()["inserted_count"] == 2
    assert response.json()["skipped_count"] == 0
    assert len(response.json()["new_jobs"]) == 2
    assert "db_path" not in response.json()


def assert_collect_run_endpoint(client: TestClient, path: str, db: Path) -> None:
    response = client.post(
        path,
        json={
            "collect": {"fixture": str(FIXTURE), "query": "python"},
            "source_query": "python",
        },
    )

    assert_inserted_two_jobs_response(response)
    assert_two_jobs_persisted(db)


def test_health_endpoint() -> None:
    client = TestClient(app)

    response = client.get("/health")

    assert response.status_code == 200
    assert response.json() == {"status": "ok"}


def test_collect_endpoint_returns_summary_only() -> None:
    client = TestClient(app)

    response = client.post("/collect", json={"fixture": str(FIXTURE)})

    assert response.status_code == 200
    payload = response.json()
    assert payload == {"record_count": 2, "query": None, "source": "fixture"}


def test_collect_jobs_preview_endpoint_returns_fixture_jobs() -> None:
    client = TestClient(app)

    response = client.post("/collect/jobs", json={"fixture": str(FIXTURE)})

    assert response.status_code == 200
    payload = response.json()
    assert payload["record_count"] == 2
    assert payload["source"] == "fixture"
    assert payload["jobs"][0]["source"] == "upwork"
    assert payload["jobs"][0]["id"]


def test_ingest_and_analytics_endpoints(tmp_path: Path, monkeypatch: pytest.MonkeyPatch) -> None:
    db = tmp_path / "upwork.sqlite"
    monkeypatch.setenv("UPWORK_APP_DB", str(db))
    client = TestClient(app)
    collect_response = client.post("/collect/jobs", json={"fixture": str(FIXTURE)})
    jobs = collect_response.json()["jobs"]
    jsonl = "".join(json.dumps(job) + "\n" for job in jobs)
    ingest_response = client.post(
        "/ingest",
        json={"jsonl": jsonl, "source_query": "python"},
    )

    assert ingest_response.status_code == 200
    assert ingest_response.json()["inserted_count"] == 2
    assert "db_path" not in ingest_response.json()

    analytics_response = client.get("/analytics/summary")

    assert analytics_response.status_code == 200
    assert analytics_response.json() == {
        "query": "summary",
        "rows": [{"jobs": 2, "skills": 4}],
    }


def test_ingest_endpoint_accepts_jobs_payload(
    tmp_path: Path, monkeypatch: pytest.MonkeyPatch
) -> None:
    db = tmp_path / "jobs-payload.sqlite"
    monkeypatch.setenv("UPWORK_APP_DB", str(db))
    client = TestClient(app)
    jobs = client.post("/collect/jobs", json={"fixture": str(FIXTURE)}).json()["jobs"]

    response = client.post("/ingest", json={"jobs": jobs, "source_query": "python"})

    assert_inserted_two_jobs_response(response)
    assert_two_jobs_persisted(db)


def test_ingest_endpoint_requires_one_payload_shape(
    tmp_path: Path, monkeypatch: pytest.MonkeyPatch
) -> None:
    monkeypatch.setenv("UPWORK_APP_DB", str(tmp_path / "invalid.sqlite"))
    client = TestClient(app)
    jobs = client.post("/collect/jobs", json={"fixture": str(FIXTURE)}).json()["jobs"]

    missing_payload = client.post("/ingest", json={"source_query": "python"})
    duplicate_payload = client.post("/ingest", json={"jsonl": "", "jobs": jobs})

    assert missing_payload.status_code == 422
    assert duplicate_payload.status_code == 422


def test_collect_and_ingest_endpoint(tmp_path: Path, monkeypatch: pytest.MonkeyPatch) -> None:
    db = tmp_path / "upwork.sqlite"
    monkeypatch.setenv("UPWORK_APP_DB", str(db))
    client = TestClient(app)

    assert_collect_run_endpoint(client, "/collect-and-ingest", db)


def test_runs_collect_endpoint_collects_new_jobs(
    tmp_path: Path, monkeypatch: pytest.MonkeyPatch
) -> None:
    db = tmp_path / "runs.sqlite"
    monkeypatch.setenv("UPWORK_APP_DB", str(db))
    client = TestClient(app)

    assert_collect_run_endpoint(client, "/runs/collect", db)


def test_http_ingest_rejects_caller_chosen_db_path(
    tmp_path: Path, monkeypatch: pytest.MonkeyPatch
) -> None:
    configured_db = tmp_path / "configured.sqlite"
    monkeypatch.setenv("UPWORK_APP_DB", str(configured_db))
    client = TestClient(app)

    attacker_db = tmp_path / "attacker.sqlite"
    response = client.post(
        "/ingest",
        json={"db_path": str(attacker_db), "jsonl": "", "source_query": "python"},
    )

    assert response.status_code == 422
    assert not attacker_db.exists()


def test_service_ingest_still_accepts_jsonl(tmp_path: Path) -> None:
    from upwork_app.services.collector import collect_from_fixture

    db = tmp_path / "service.sqlite"
    records = read_jsonl(__import__("io").StringIO(jobs_to_jsonl(collect_from_fixture(FIXTURE))))
    result = ingest_records(records, db_path=str(db), input_path=None, source_query="python")

    assert result.inserted_count == 2
