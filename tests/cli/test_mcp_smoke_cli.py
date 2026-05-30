from __future__ import annotations

from typing import Any

import pytest

from work_feed_mcp.cli import mcp_smoke


class FakeToolResult:
    def __init__(self, *, is_error: bool = False, structured: dict[str, Any] | None = None) -> None:
        self.isError = is_error
        self.structuredContent = structured

    def model_dump(self, *, mode: str) -> dict[str, Any]:
        return {"mode": mode, "structuredContent": self.structuredContent, "isError": self.isError}


def test_mcp_smoke_rejects_limit_above_service_contract(capsys: Any) -> None:
    result = mcp_smoke.main(["--url", "http://127.0.0.1:1/mcp", "--limit", "101"])

    assert result == 2
    assert "limit must be <= 100" in capsys.readouterr().err


def test_mcp_smoke_default_url_uses_runtime_port_and_path(monkeypatch: pytest.MonkeyPatch) -> None:
    monkeypatch.setenv("WORK_FEED_MCP_PORT", "8123")
    monkeypatch.setenv("WORK_FEED_MCP_PATH", "/custom-mcp")

    assert mcp_smoke.default_smoke_url() == "http://127.0.0.1:8123/custom-mcp"


def test_mcp_smoke_rejects_tool_error_result() -> None:
    tool_result = FakeToolResult(is_error=True, structured={"ok": True})

    try:
        mcp_smoke._assert_tool_success(tool_result)
    except mcp_smoke.McpSmokeUsageError as exc:
        assert "MCP tool error" in str(exc)
    else:  # pragma: no cover - assertion guard
        raise AssertionError("expected tool error")


def test_mcp_smoke_rejects_structured_ok_false() -> None:
    tool_result = FakeToolResult(structured={"ok": False, "error": "invalid_request"})

    try:
        mcp_smoke._assert_tool_success(tool_result)
    except mcp_smoke.McpSmokeUsageError as exc:
        assert "invalid_request" in str(exc)
    else:  # pragma: no cover - assertion guard
        raise AssertionError("expected ok=false error")


def test_mcp_smoke_preserves_structured_failure_reason_and_next_action() -> None:
    tool_result = FakeToolResult(
        structured={
            "ok": False,
            "error": "not_ready",
            "reason": "unsupported_schema",
            "next_action": "upgrade work-feed or migrate the database",
        }
    )

    try:
        mcp_smoke._assert_tool_success(tool_result)
    except mcp_smoke.McpSmokeUsageError as exc:
        message = str(exc)
        assert "unsupported_schema" in message
        assert "upgrade work-feed or migrate the database" in message
    else:  # pragma: no cover - assertion guard
        raise AssertionError("expected ok=false error")


def test_mcp_smoke_root_error_message_unwraps_exception_group() -> None:
    error = ExceptionGroup("outer", [ConnectionRefusedError("connection refused")])

    assert mcp_smoke._root_error_message(error) == "connection refused"
