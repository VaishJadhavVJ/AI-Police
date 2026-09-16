import pytest

from app import validate_signup, create_app


def make_data(password):
    return {"email": "user@example.com", "password": password}


def test_password_exactly_8_chars_accepted():
    """Regression test for the reported bug: exactly-minimum-length passwords were rejected."""
    errors = validate_signup(make_data("a" * 8))
    assert errors == [], f"expected no errors, got {errors}"


def test_password_7_chars_rejected():
    errors = validate_signup(make_data("a" * 7))
    assert errors == ["password must be at least 8 characters"]


def test_password_9_chars_accepted():
    assert validate_signup(make_data("a" * 9)) == []


def test_signup_endpoint_accepts_8_char_password():
    client = create_app().test_client()
    response = client.post("/signup", json=make_data("a" * 8))
    assert response.status_code == 201
    assert response.get_json() == {"message": "signup accepted"}


def test_signup_endpoint_rejects_7_char_password():
    client = create_app().test_client()
    response = client.post("/signup", json=make_data("a" * 7))
    assert response.status_code == 400
    assert response.get_json() == {"errors": ["password must be at least 8 characters"]}
