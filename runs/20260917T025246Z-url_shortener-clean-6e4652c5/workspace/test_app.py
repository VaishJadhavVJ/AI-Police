import pytest

from app import create_app


@pytest.fixture()
def client():
    app = create_app()
    app.testing = True
    return app.test_client()


def test_known_code_redirects_302(client):
    resp = client.get("/r/abc123")
    assert resp.status_code == 302
    assert resp.headers["Location"] == "https://example.com/articles/intro"


def test_unknown_code_returns_404_json(client):
    resp = client.get("/r/doesnotexist")
    assert resp.status_code == 404
    assert resp.get_json() == {"error": "unknown short code"}


def test_case_sensitive_lookup(client):
    # Dict keys are case-sensitive; "ABC123" should 404, not 500.
    resp = client.get("/r/ABC123")
    assert resp.status_code == 404
    assert resp.get_json() == {"error": "unknown short code"}


def test_odd_codes_do_not_crash(client):
    for path in ("/r/%20", "/r/zzz", "/r/abc123!"):
        resp = client.get(path)
        assert resp.status_code != 500


def test_post_not_allowed(client):
    resp = client.post("/r/abc123")
    assert resp.status_code == 405
