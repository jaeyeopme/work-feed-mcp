"""Compatibility shim for Upwork credential helpers."""

from upwork_app.integrations.upwork.credentials import (
    CredentialReferences,
    SecretValue,
    load_credential_references,
    redact,
)

__all__ = ["CredentialReferences", "SecretValue", "load_credential_references", "redact"]
