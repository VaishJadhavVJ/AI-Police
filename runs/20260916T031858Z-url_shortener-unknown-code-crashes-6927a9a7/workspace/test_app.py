import pytest

from app import create_app


@pytest.fixture()
def client():
    return create_app().test_client()


def test_unknown_code_returns_404_json(client):
    resp = client.get("/r/doesnotexist")
    assert resp.status_code == 404
    assert resp.get_json() == {"error": "unknown short code"}


def test_known_code_redirects(client):
    resp = client.get("/r/abc123")
    assert resp.status_code == 302
    assert resp.headers["Location"] == "https://example.com/articles/intro"
