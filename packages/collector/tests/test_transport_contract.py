from __future__ import annotations

from http.cookiejar import Cookie, CookieJar

from upwork_collector.transport import _extract_visitor_token


def _cookie(name: str, value: str) -> Cookie:
    return Cookie(
        version=0,
        name=name,
        value=value,
        port=None,
        port_specified=False,
        domain=".upwork.com",
        domain_specified=True,
        domain_initial_dot=True,
        path="/",
        path_specified=True,
        secure=True,
        expires=None,
        discard=True,
        comment=None,
        comment_url=None,
        rest={},
        rfc2109=False,
    )


def test_extracts_visitor_token_from_bootstrap_cookie_jar() -> None:
    jar = CookieJar()
    jar.set_cookie(_cookie("visitor_gql_token", "visitor-token-value"))

    assert _extract_visitor_token(jar) == "visitor-token-value"


def test_extracts_visitor_token_from_supplied_cookie_header() -> None:
    jar = CookieJar()

    assert (
        _extract_visitor_token(jar, "other=value; visitor_gql_token=visitor-token-value; x=y")
        == "visitor-token-value"
    )
