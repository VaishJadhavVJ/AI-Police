import pytest

from app import create_app


@pytest.fixture
def client():
    app = create_app()
    return app.test_client()


def test_existing_code_redirects(client):
    r = client.get("/r/abc123")
    assert r.status_code == 302
    assert r.headers["Location"] == "https://example.com/articles/intro"


def test_unknown_code_returns_404(client):
    r = client.get("/r/doesnotexist")
    assert r.status_code == 404
    assert r.get_json() == {"error": "unknown short code"}


def test_unknown_code_is_not_500(client):
    assert client.get("/r/doesnotexist").status_code != 500
