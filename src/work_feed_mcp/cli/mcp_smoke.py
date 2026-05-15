"""Protocol-level MCP smoke check for a running work-feed server."""

from __future__ import annotations

import argparse
import asyncio
import json
import sys
from collections.abc import Sequence
from typing import Any, Never

from mcp import ClientSession
from mcp.client.streamable_http import streamable_http_client

from work_feed_mcp.services.limits import validate_limit


class McpSmokeUsageError(Exception):
    """Raised for invalid smoke-check arguments."""


class McpSmokeArgumentParser(argparse.ArgumentParser):
    def error(self, message: str) -> Never:
        raise McpSmokeUsageError(message)


def build_parser() -> argparse.ArgumentParser:
    parser = McpSmokeArgumentParser(prog="work-feed mcp-smoke")
    parser.add_argument("--url", default="http://127.0.0.1:8000/mcp")
    parser.add_argument("--limit", type=int, default=5)
    return parser


async def smoke_mcp(url: str, *, limit: int = 5) -> dict[str, Any]:
    """Initialize MCP, list tools, and call jobs_recent against a live server."""

    resolved_limit = validate_limit(limit)
    async with (
        streamable_http_client(url) as (read_stream, write_stream, _session_id),
        ClientSession(read_stream, write_stream) as session,
    ):
        await session.initialize()
        tools = await session.list_tools()
        tool_names = sorted(tool.name for tool in tools.tools)
        if "jobs_recent" not in tool_names:
            raise McpSmokeUsageError("jobs_recent tool is not exposed by MCP server")
        result = await session.call_tool("jobs_recent", {"limit": resolved_limit})
        result_payload = _assert_tool_success(result)
        return {
            "ok": True,
            "url": url,
            "tools": tool_names,
            "jobs_recent": result_payload,
        }


def _assert_tool_success(result: Any) -> dict[str, Any]:
    dumped = result.model_dump(mode="json") if hasattr(result, "model_dump") else {}
    if bool(getattr(result, "isError", False)):
        raise McpSmokeUsageError("jobs_recent returned an MCP tool error")
    structured = getattr(result, "structuredContent", None)
    if isinstance(structured, dict) and structured.get("ok") is False:
        detail = structured.get("message") or structured.get("reason") or structured.get("error")
        if next_action := structured.get("next_action"):
            detail = (
                f"{detail}; next_action={next_action}" if detail else f"next_action={next_action}"
            )
        raise McpSmokeUsageError(f"jobs_recent failed: {detail or 'tool returned ok=false'}")
    return dumped if isinstance(dumped, dict) else {"result": dumped}


def _root_error_message(error: BaseException) -> str:
    if isinstance(error, ExceptionGroup):
        if not error.exceptions:
            return str(error)
        return _root_error_message(error.exceptions[0])
    cause = error.__cause__ or error.__context__
    if cause is not None:
        return _root_error_message(cause)
    message = str(error)
    return message or type(error).__name__


def main(argv: Sequence[str] | None = None) -> int:
    try:
        args = build_parser().parse_args(argv)
        result = asyncio.run(smoke_mcp(args.url, limit=args.limit))
        print(json.dumps(result, sort_keys=True))
        return 0
    except (McpSmokeUsageError, ValueError) as exc:
        print(str(exc), file=sys.stderr)
        return 2
    except Exception as exc:
        print(f"MCP smoke failed: {_root_error_message(exc)}", file=sys.stderr)
        return 1


if __name__ == "__main__":
    raise SystemExit(main())
