"""Compatibility shim for ingest errors."""

from upwork_app.core.errors import (
    ExitCode,
    IngestError,
    UsageError,
    ValidationError,
    exit_code_for_error,
)

__all__ = ["ExitCode", "IngestError", "UsageError", "ValidationError", "exit_code_for_error"]
