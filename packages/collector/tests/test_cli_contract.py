from __future__ import annotations

import json
from pathlib import Path

from upwork_collector.cli import build_parser, main
from upwork_collector.errors import ExitCode


def test_fixture_collect_emits_jsonl_stdout_only(capsys) -> None:  # type: ignore[no-untyped-def]
    code = main(["collect", "--fixture", "tests/fixtures/visitor_job_search_response.json"])
    captured = capsys.readouterr()

    assert code == ExitCode.SUCCESS
    lines = [line for line in captured.out.splitlines() if line.strip()]
    assert len(lines) == 2
    assert all(json.loads(line)["source"] == "upwork" for line in lines)
    assert "title" not in captured.err.lower()


def test_invalid_cli_options_exit_usage_error(capsys) -> None:  # type: ignore[no-untyped-def]
    code = main(
        [
            "collect",
            "--fixture",
            "tests/fixtures/visitor_job_search_response.json",
            "--live",
        ]
    )
    captured = capsys.readouterr()

    assert code == ExitCode.USAGE_ERROR
    assert captured.out == ""


def test_invalid_page_size_exits_usage_error(capsys) -> None:  # type: ignore[no-untyped-def]
    code = main(
        [
            "collect",
            "--fixture",
            "tests/fixtures/visitor_job_search_response.json",
            "--page-size",
            "0",
        ]
    )
    captured = capsys.readouterr()

    assert code == ExitCode.USAGE_ERROR
    assert captured.out == ""


def test_live_cli_defaults_to_one_page_of_fifty() -> None:
    parser = build_parser()

    live_args = parser.parse_args(["live-smoke", "--query", "python"])
    collect_args = parser.parse_args(["collect", "--live", "--query", "python"])

    assert live_args.max_pages == 1
    assert live_args.page_size == 50
    assert collect_args.max_pages == 1
    assert collect_args.page_size == 50


def test_malformed_fixture_maps_to_schema_failure(capsys) -> None:  # type: ignore[no-untyped-def]
    code = main(["collect", "--fixture", "tests/fixtures/malformed_response.json"])
    captured = capsys.readouterr()

    assert code == ExitCode.UPSTREAM_SCHEMA_OR_TEMPORARY_FAILURE
    assert captured.out == ""


def test_live_smoke_requires_explicit_enablement(monkeypatch, capsys) -> None:  # type: ignore[no-untyped-def]
    monkeypatch.delenv("UPWORK_COLLECTOR_LIVE", raising=False)

    code = main(["live-smoke", "--query", "python"])
    captured = capsys.readouterr()

    assert code == ExitCode.CREDENTIAL_REQUIRED
    assert captured.out == ""
    assert "UPWORK_COLLECTOR_LIVE=1" in captured.err


def test_cli_does_not_create_default_state_files(tmp_path: Path, monkeypatch, capsys) -> None:  # type: ignore[no-untyped-def]
    monkeypatch.chdir(tmp_path)
    fixture = Path(__file__).parent / "fixtures" / "visitor_job_search_response.json"

    code = main(["collect", "--fixture", str(fixture)])
    capsys.readouterr()

    assert code == ExitCode.SUCCESS
    forbidden = list(tmp_path.glob("*.sqlite")) + list(tmp_path.glob("snapshot-*.json"))
    assert forbidden == []


def test_cli_boundary_redacts_unexpected_secret_errors(monkeypatch, capsys) -> None:  # type: ignore[no-untyped-def]
    def boom(_response: dict[str, object]) -> int:
        raise RuntimeError("Bearer " + "abc.def_123" + " leaked")

    monkeypatch.setattr("upwork_collector.cli._emit_jobs_from_response", boom)

    code = main(["collect", "--fixture", "tests/fixtures/visitor_job_search_response.json"])
    captured = capsys.readouterr()

    assert code == ExitCode.INTERNAL_FAILURE
    assert "abc.def_123" not in captured.err
    assert "<redacted>" in captured.err


def test_invalid_live_cookie_reference_exits_credential_required(
    monkeypatch, tmp_path, capsys
) -> None:  # type: ignore[no-untyped-def]
    monkeypatch.setenv("UPWORK_COLLECTOR_LIVE", "1")
    monkeypatch.setenv("UPWORK_COLLECTOR_COOKIE_FILE", str(tmp_path / "missing-cookie.txt"))

    code = main(["live-smoke", "--query", "python"])
    captured = capsys.readouterr()

    assert code == ExitCode.CREDENTIAL_REQUIRED
    assert captured.out == ""
    assert str(tmp_path) not in captured.err


def test_missing_fixture_path_exits_usage_error(capsys) -> None:  # type: ignore[no-untyped-def]
    code = main(["collect", "--fixture", "/tmp/upwork-collector-missing-fixture.json"])
    captured = capsys.readouterr()

    assert code == ExitCode.USAGE_ERROR
    assert captured.out == ""


def test_invalid_fixture_json_exits_usage_error(tmp_path, capsys) -> None:  # type: ignore[no-untyped-def]
    fixture = tmp_path / "invalid.json"
    fixture.write_text("not-json", encoding="utf-8")

    code = main(["collect", "--fixture", str(fixture)])
    captured = capsys.readouterr()

    assert code == ExitCode.USAGE_ERROR
    assert captured.out == ""


def test_collect_live_requires_env_gate(monkeypatch, capsys) -> None:  # type: ignore[no-untyped-def]
    monkeypatch.delenv("UPWORK_COLLECTOR_LIVE", raising=False)

    code = main(["collect", "--live", "--query", "python"])
    captured = capsys.readouterr()

    assert code == ExitCode.CREDENTIAL_REQUIRED
    assert captured.out == ""
    assert "UPWORK_COLLECTOR_LIVE=1" in captured.err
