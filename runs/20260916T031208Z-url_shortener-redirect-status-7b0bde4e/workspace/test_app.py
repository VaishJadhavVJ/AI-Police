from app import app


def test_unknown_code_is_404_json():
    client = app.test_client()
    resp = client.get("/r/does-not-exist")
    assert resp.status_code == 404
    assert resp.get_json() == {"error": "unknown short code"}


def test_known_code_returns_successful_json_response():
    client = app.test_client()
    resp = client.get("/r/abc123")

    assert resp.status_code == 200
    assert resp.content_type.startswith("application/json")
    assert resp.get_json() == {"url": "https://example.com/articles/intro"}


def test_known_code_is_not_a_redirect():
    client = app.test_client()
    resp = client.get("/r/abc123", follow_redirects=False)

    # Must not be a redirect status, must not carry a Location header,
    # and must not be Werkzeug's HTML "Redirecting..." page.
    assert not 300 <= resp.status_code < 400
    assert "Location" not in resp.headers
    body = resp.get_data(as_text=True)
    assert "Redirecting" not in body
    assert "text/html" not in resp.headers.get("Content-Type", "")
