"""Regression tests for the short-link redirect behavior."""
import pytest

from app import create_app, SHORT_URLS


@pytest.fixture()
def client():
    return create_app().test_client()


def test_known_code_redirects_to_target(client):
    response = client.get("/r/abc123")
    assert response.status_code in (301, 302, 303, 307, 308)
    assert response.headers["Location"] == SHORT_URLS["abc123"]


def test_unknown_code_returns_404(client):
    response = client.get("/r/nope")
    assert response.status_code == 404
    assert response.get_json() == {"error": "unknown short code"}
