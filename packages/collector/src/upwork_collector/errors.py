"""Compatibility shim for collector errors."""

from upwork_app.integrations.upwork.errors import (
    CollectorError,
    CredentialRequiredError,
    ExitCode,
    InternalFailureError,
    RateLimitedError,
    UpstreamBlockedError,
    UpstreamSchemaOrTemporaryError,
    UsageError,
    exit_code_for_error,
)

__all__ = [
    "CollectorError",
    "CredentialRequiredError",
    "ExitCode",
    "InternalFailureError",
    "RateLimitedError",
    "UpstreamBlockedError",
    "UpstreamSchemaOrTemporaryError",
    "UsageError",
    "exit_code_for_error",
]
