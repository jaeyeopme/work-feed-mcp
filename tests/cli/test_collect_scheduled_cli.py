from __future__ import annotations

import json
from pathlib import Path
from typing import Any

import pytest

from upwork_app.cli import __main__, collect_scheduled
from upwork_app.integrations.upwork.errors import UpstreamBlockedError
from upwork_app.services.scheduled_collection import ScheduledCollectionResult, ScheduledQueryResult


def test_collect_scheduled_cli_outputs_summary(
    monkeypatch: pytest.MonkeyPatch,
    capsys: pytest.CaptureFixture[str],
    tmp_path: Path,
) -> None:
    seen: dict[str, Any] = {}

    def fake_collect_scheduled(**kwargs: Any) -> ScheduledCollectionResult:
        seen.update(kwargs)
        return ScheduledCollectionResult(
            db_path=kwargs["db_path"],
            query_count=len(kwargs["queries"]),
            results=(
                ScheduledQueryResult(
                    query="python",
                    seen_count=50,
                    inserted_count=10,
                    skipped_count=40,
                    new_jobs=(),
                ),
                ScheduledQueryResult(
                    query="scraping",
                    seen_count=50,
                    inserted_count=8,
                    skipped_count=42,
                    new_jobs=(),
                ),
            ),
        )

    monkeypatch.setattr(collect_scheduled, "collect_scheduled", fake_collect_scheduled)

    assert (
        collect_scheduled.main(
            [
                "--db",
                str(tmp_path / "upwork.sqlite"),
                "--queries",
                "python, scraping",
                "--max-pages",
                "1",
                "--page-size",
                "50",
            ]
        )
        == 0
    )

    assert seen["queries"] == ("python", "scraping")
    payload = json.loads(capsys.readouterr().out)
    assert payload["query_count"] == 2
    assert [item["query"] for item in payload["results"]] == ["python", "scraping"]


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
