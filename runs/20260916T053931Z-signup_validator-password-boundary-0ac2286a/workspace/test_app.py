from app import validate_signup, create_app


def test_password_exactly_8_chars_is_accepted():
    data = {"email": "user@example.com", "password": "12345678"}
    assert validate_signup(data) == []


def test_password_shorter_than_8_chars_is_rejected():
    data = {"email": "user@example.com", "password": "1234567"}
    assert "password must be at least 8 characters" in validate_signup(data)


def test_password_longer_than_8_chars_is_accepted():
    data = {"email": "user@example.com", "password": "123456789"}
    assert validate_signup(data) == []


def test_signup_endpoint_accepts_8_char_password():
    client = create_app().test_client()
    resp = client.post(
        "/signup", json={"email": "user@example.com", "password": "12345678"}
    )
    assert resp.status_code == 201
    assert resp.get_json() == {"message": "signup accepted"}


def test_signup_endpoint_rejects_7_char_password():
    client = create_app().test_client()
    resp = client.post(
        "/signup", json={"email": "user@example.com", "password": "1234567"}
    )
    assert resp.status_code == 400
    assert "password must be at least 8 characters" in resp.get_json()["errors"]
