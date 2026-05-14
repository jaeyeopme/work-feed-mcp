"""Local proxy reference loading and redaction helpers."""

from __future__ import annotations

import os
import re
from collections.abc import Mapping
from dataclasses import dataclass
from pathlib import Path

_HEADER_SECRET_PATTERNS: tuple[re.Pattern[str], ...] = (
    re.compile(r"(?im)^(\s*(?:cookie|set-cookie|session)\s*:\s*).*$"),
)

_SECRET_PATTERNS: tuple[re.Pattern[str], ...] = (
    re.compile(r"Bearer\s+[A-Za-z0-9._\-]+"),
    re.compile(r"https?://[^\s:/]+:[^\s@]+@[^\s]+"),
    re.compile(r"(?i)(visitor_gql_token=)[^;\s]+"),
    re.compile(r"(?i)((?:cookie|session|token)\s*=\s*)[^;\s]+(?:;\s*[^;\s=]+=[^;\s]+)*"),
)

_ENV_SECRET_NAMES = ("UPWORK_COLLECTOR_PROXY_URL",)


@dataclass(frozen=True, slots=True)
class SecretValue:
    label: str
    value: str

    def __str__(self) -> str:
        return f"{self.label}=<redacted>"

    def __repr__(self) -> str:
        return f"SecretValue(label={self.label!r}, value='<redacted>')"


@dataclass(frozen=True, slots=True)
class CredentialReferences:
    proxy_url: SecretValue | None = None

    @property
    def has_any(self) -> bool:
        return self.proxy_url is not None


def redact(text: object, env: Mapping[str, str] | None = None) -> str:
    """Mask known secret-like values in diagnostic text."""

    redacted = str(text)
    for pattern in _HEADER_SECRET_PATTERNS:
        redacted = pattern.sub(lambda match: f"{match.group(1)}<redacted>", redacted)
    for pattern in _SECRET_PATTERNS:
        redacted = pattern.sub(
            lambda match: f"{match.group(1)}<redacted>" if match.groups() else "<redacted>",
            redacted,
        )

    source = os.environ if env is None else env
    for name in _ENV_SECRET_NAMES:
        value = source.get(name)
        if value:
            redacted = redacted.replace(value, "<redacted>")
            path = Path(value)
            if path.exists() and path.is_file():
                try:
                    content = path.read_text(encoding="utf-8").strip()
                except OSError:
                    content = ""
                if content:
                    redacted = redacted.replace(content, "<redacted>")
    return redacted


def load_credential_references(env: Mapping[str, str] | None = None) -> CredentialReferences:
    source = os.environ if env is None else env
    proxy = None
    if proxy_url := source.get("UPWORK_COLLECTOR_PROXY_URL"):
        proxy = SecretValue(label="proxy_url", value=proxy_url)
    return CredentialReferences(proxy_url=proxy)
