from __future__ import annotations

import json
from pathlib import Path
from typing import Any

import pytest

from upwork_app.cli import __main__, collect_scheduled
from upwork_app.integrations.upwork.errors import UpstreamBlockedError
from upwork_app.services.scheduled_collection import ScheduledCollectionResult, ScheduledQueryResult


def _result(
    *,
    db_path: str,
    query_count: int,
    run_id: str,
    results: tuple[ScheduledQueryResult, ...],
) -> ScheduledCollectionResult:
    return ScheduledCollectionResult(
        db_path=db_path,
        query_count=query_count,
        run_id=run_id,
        results=results,
    )


def _run_collect_scheduled_with_fake(
    monkeypatch: pytest.MonkeyPatch,
    argv: list[str],
    result: ScheduledCollectionResult,
) -> dict[str, Any]:
    seen: dict[str, Any] = {}

    def fake_collect_scheduled(**kwargs: Any) -> ScheduledCollectionResult:
        seen.update(kwargs)
        return result

    monkeypatch.setattr(collect_scheduled, "collect_scheduled", fake_collect_scheduled)
    assert collect_scheduled.main(argv) == 0
    return seen


def test_collect_scheduled_cli_outputs_summary(
    monkeypatch: pytest.MonkeyPatch,
    capsys: pytest.CaptureFixture[str],
    tmp_path: Path,
) -> None:
    result = _result(
        db_path=str(tmp_path / "upwork.sqlite"),
        query_count=2,
        run_id="run-1",
        results=(
            ScheduledQueryResult("python", 50, 10, 40),
            ScheduledQueryResult("scraping", 50, 8, 42),
        ),
    )
    seen = _run_collect_scheduled_with_fake(
        monkeypatch,
        [
            "--db",
            str(tmp_path / "upwork.sqlite"),
            "--queries",
            "python, scraping",
            "--max-pages",
            "1",
            "--page-size",
            "50",
        ],
        result,
    )

    assert seen["queries"] == ("python", "scraping")
    payload = json.loads(capsys.readouterr().out)
    assert payload["query_count"] == 2
    assert payload["run_id"] == "run-1"
    assert [item["query"] for item in payload["results"]] == ["python", "scraping"]


def test_collect_scheduled_cli_defaults_to_unfiltered_collection(
    monkeypatch: pytest.MonkeyPatch,
    capsys: pytest.CaptureFixture[str],
    tmp_path: Path,
) -> None:
    result = _result(
        db_path=str(tmp_path / "upwork.sqlite"),
        query_count=1,
        run_id="run-default",
        results=(ScheduledQueryResult(None, 250, 17, 233),),
    )
    seen = _run_collect_scheduled_with_fake(
        monkeypatch,
        ["--db", str(tmp_path / "upwork.sqlite"), "--max-pages", "5", "--page-size", "50"],
        result,
    )

    assert seen["queries"] is None
    payload = json.loads(capsys.readouterr().out)
    assert payload["query_count"] == 1
    assert payload["results"][0]["query"] is None


def test_collect_scheduled_cli_rejects_empty_queries(
    capsys: pytest.CaptureFixture[str],
) -> None:
    assert collect_scheduled.main(["--db", "x.sqlite", "--queries", ",,"]) == 2
    assert "--queries must contain at least one query" in capsys.readouterr().err


def test_collect_scheduled_cli_redacts_collector_errors(
    monkeypatch: pytest.MonkeyPatch,
    capsys: pytest.CaptureFixture[str],
) -> None:
    def fake_collect_scheduled(**kwargs: Any) -> ScheduledCollectionResult:
        raise UpstreamBlockedError("blocked token=secret")

    monkeypatch.setattr(collect_scheduled, "collect_scheduled", fake_collect_scheduled)

    assert collect_scheduled.main(["--db", "x.sqlite", "--queries", "python"]) == 20
    captured = capsys.readouterr()
    assert "token=<redacted>" in captured.err
    assert "secret" not in captured.err


def test_top_level_cli_dispatches_collect_scheduled(
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    called: list[list[str]] = []

    def fake_main(argv: list[str]) -> int:
        called.append(argv)
        return 0

    monkeypatch.setattr(collect_scheduled, "main", fake_main)

    assert __main__.main(["collect-scheduled", "--db", "x", "--queries", "python"]) == 0
    assert called == [["--db", "x", "--queries", "python"]]


def test_top_level_cli_dispatches_scheduler_status(
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    from upwork_app.cli import scheduler_status

    called: list[list[str]] = []

    def fake_main(argv: list[str]) -> int:
        called.append(argv)
        return 0

    monkeypatch.setattr(scheduler_status, "main", fake_main)

    assert __main__.main(["scheduler-status", "--db", "x"]) == 0
    assert called == [["--db", "x"]]
