import pytest

from app import create_app


@pytest.fixture()
def client():
    return create_app().test_client()


def test_known_code_redirects(client):
    r = client.get("/r/abc123")
    assert r.status_code == 301
    assert r.headers["Location"] == "https://example.com/articles/intro"


def test_unknown_code_returns_json_404(client):
    r = client.get("/r/does-not-exist")
    assert r.status_code == 404
    assert r.get_json() == {"error": "unknown short code"}


def test_unsafe_scheme_is_rejected(client, monkeypatch):
    from app import SHORT_URLS

    monkeypatch.setitem(SHORT_URLS, "evil", "javascript:alert(1)")
    r = client.get("/r/evil")
    assert r.status_code == 400


def test_protocol_relative_url_is_rejected(client, monkeypatch):
    from app import SHORT_URLS

    monkeypatch.setitem(SHORT_URLS, "pr", "//evil.example/steal")
    r = client.get("/r/pr")
    assert r.status_code == 400


def test_http_targets_are_allowed(client, monkeypatch):
    from app import SHORT_URLS

    monkeypatch.setitem(SHORT_URLS, "plain", "http://example.com/page")
    r = client.get("/r/plain")
    assert r.status_code == 301
    assert r.headers["Location"] == "http://example.com/page"
