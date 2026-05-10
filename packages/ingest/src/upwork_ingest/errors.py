"""Typed ingest errors and stable CLI exit codes."""

from __future__ import annotations

from dataclasses import dataclass
from enum import IntEnum


class ExitCode(IntEnum):
    SUCCESS = 0
    USAGE_ERROR = 2
    VALIDATION_ERROR = 30
    INTERNAL_FAILURE = 40


@dataclass(slots=True)
class IngestError(Exception):
    message: str
    code: ExitCode

    def __str__(self) -> str:
        return self.message


class UsageError(IngestError):
    def __init__(self, message: str) -> None:
        super().__init__(message, ExitCode.USAGE_ERROR)


class ValidationError(IngestError):
    def __init__(self, message: str) -> None:
        super().__init__(message, ExitCode.VALIDATION_ERROR)


def exit_code_for_error(error: BaseException) -> int:
    if isinstance(error, IngestError):
        return int(error.code)
    return int(ExitCode.INTERNAL_FAILURE)
