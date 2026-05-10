"""Typed errors and stable process exit-code mapping."""

from __future__ import annotations

from dataclasses import dataclass
from enum import IntEnum


class ExitCode(IntEnum):
    SUCCESS = 0
    USAGE_ERROR = 2
    CREDENTIAL_REQUIRED = 10
    UPSTREAM_BLOCKED = 20
    RATE_LIMITED = 21
    UPSTREAM_SCHEMA_OR_TEMPORARY_FAILURE = 30
    INTERNAL_FAILURE = 40


@dataclass(slots=True)
class CollectorError(Exception):
    """Base class for expected collector failures."""

    message: str
    code: ExitCode

    def __str__(self) -> str:
        return self.message


class UsageError(CollectorError):
    def __init__(self, message: str) -> None:
        super().__init__(message, ExitCode.USAGE_ERROR)


class CredentialRequiredError(CollectorError):
    def __init__(
        self, message: str = "live collection requires explicit local credentials"
    ) -> None:
        super().__init__(message, ExitCode.CREDENTIAL_REQUIRED)


class UpstreamBlockedError(CollectorError):
    def __init__(self, message: str = "upstream blocked or denied the request") -> None:
        super().__init__(message, ExitCode.UPSTREAM_BLOCKED)


class RateLimitedError(CollectorError):
    def __init__(self, message: str = "upstream rate limited the request") -> None:
        super().__init__(message, ExitCode.RATE_LIMITED)


class UpstreamSchemaOrTemporaryError(CollectorError):
    def __init__(
        self, message: str = "upstream response was malformed or temporarily unavailable"
    ) -> None:
        super().__init__(message, ExitCode.UPSTREAM_SCHEMA_OR_TEMPORARY_FAILURE)


class InternalFailureError(CollectorError):
    def __init__(self, message: str = "unexpected internal failure") -> None:
        super().__init__(message, ExitCode.INTERNAL_FAILURE)


def exit_code_for_error(error: BaseException) -> int:
    """Return the stable process exit code for an error."""

    if isinstance(error, CollectorError):
        return int(error.code)
    return int(ExitCode.INTERNAL_FAILURE)
