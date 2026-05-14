from __future__ import annotations

from upwork_app.integrations.upwork.credentials import (
    SecretValue,
    load_credential_references,
    redact,
)


def test_fixture_style_paths_do_not_require_credentials() -> None:
    refs = load_credential_references({})
    assert not refs.has_any


def test_proxy_reference_loads_without_printing_raw_value() -> None:
    refs = load_credential_references(
        {"UPWORK_COLLECTOR_PROXY_URL": "https://" + "user:pass" + "@example.test:8080"}
    )

    assert refs.proxy_url is not None
    assert "user:pass" not in str(refs.proxy_url)
    assert "user:pass" not in repr(refs.proxy_url)


def test_redacts_cookie_bearer_proxy_and_env_values() -> None:
    env = {"UPWORK_COLLECTOR_PROXY_URL": "https://" + "user:pass" + "@example.test:8080"}
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


def test_redacts_multi_value_cookie_and_session_headers() -> None:
    redacted = redact("Cookie: a=secret1; b=secret2\nSession: c=secret3; d=secret4")

    assert "secret1" not in redacted
    assert "secret2" not in redacted
    assert "secret3" not in redacted
    assert "secret4" not in redacted
    assert redacted.count("<redacted>") == 2


def test_redacts_live_diagnostic_material_from_error_text() -> None:
    env = {"UPWORK_COLLECTOR_PROXY_URL": "http://user:pass@example.test:8080"}

    redacted = redact(
        "upstream network failure: Cookie: visitor_gql_token=secret-token; "
        "proxy=http://user:pass@example.test:8080 Bearer secret-token",
        env,
    )

    assert "secret-token" not in redacted
    assert "user:pass" not in redacted
