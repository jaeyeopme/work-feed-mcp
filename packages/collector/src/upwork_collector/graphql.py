"""Compatibility shim for Upwork GraphQL helpers."""

from upwork_app.integrations.upwork.graphql import (
    ENDPOINT,
    QUERY_DOCUMENT,
    build_request_payload,
    extract_results,
)

__all__ = ["ENDPOINT", "QUERY_DOCUMENT", "build_request_payload", "extract_results"]
