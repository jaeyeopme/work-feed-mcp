from __future__ import annotations

from pathlib import Path

import pytest

from upwork_collector.credentials import SecretValue, load_credential_references, redact
from upwork_collector.errors import CredentialRequiredError


def test_fixture_style_paths_do_not_require_credentials() -> None:
    refs = load_credential_references({})
    assert not refs.has_any


def test_local_file_reference_loads_without_printing_raw_value(tmp_path: Path) -> None:
    cookie_file = tmp_path / "cookie.txt"
    cookie_file.write_text("cookie: super-secret-cookie", encoding="utf-8")

    refs = load_credential_references({"UPWORK_COLLECTOR_COOKIE_FILE": str(cookie_file)})

    assert refs.cookie is not None
    assert refs.cookie.value == "cookie: super-secret-cookie"
    assert "super-secret-cookie" not in str(refs.cookie)
    assert "super-secret-cookie" not in repr(refs.cookie)


def test_redacts_cookie_bearer_proxy_and_env_values(tmp_path: Path) -> None:
    session_file = tmp_path / "session.txt"
    session_file.write_text("session=raw-session-value", encoding="utf-8")
    env = {
        "UPWORK_COLLECTOR_SESSION_FILE": str(session_file),
        "UPWORK_COLLECTOR_PROXY_URL": "https://" + "user:pass" + "@example.test:8080",
    }
    text = (
        "Bearer "
        + "abc.def_123"
        + " visitor_gql_token="
        + "token123 "
        + "https://"
        + "user:pass"
        + "@example.test:8080 session=raw-session-value"
    )

    redacted = redact(text, env)

    assert "abc.def_123" not in redacted
    assert "token123" not in redacted
    assert "user:pass" not in redacted
    assert "raw-session-value" not in redacted


def test_secret_value_repr_is_redacted() -> None:
    secret = SecretValue(label="proxy", value="https://" + "user:pass" + "@example.test")
    assert "user:pass" not in repr(secret)
    assert "user:pass" not in str(secret)


def test_missing_secret_file_maps_to_credential_required(tmp_path: Path) -> None:
    missing = tmp_path / "missing-cookie.txt"

    with pytest.raises(CredentialRequiredError):
        load_credential_references({"UPWORK_COLLECTOR_COOKIE_FILE": str(missing)})


def test_empty_secret_file_maps_to_credential_required(tmp_path: Path) -> None:
    empty = tmp_path / "cookie.txt"
    empty.write_text("", encoding="utf-8")

    with pytest.raises(CredentialRequiredError):
        load_credential_references({"UPWORK_COLLECTOR_COOKIE_FILE": str(empty)})


def test_redacts_multi_value_cookie_and_session_headers() -> None:
    redacted = redact("Cookie: a=secret1; b=secret2\nSession: c=secret3; d=secret4")

    assert "secret1" not in redacted
    assert "secret2" not in redacted
    assert "secret3" not in redacted
    assert "secret4" not in redacted
    assert redacted.count("<redacted>") == 2
