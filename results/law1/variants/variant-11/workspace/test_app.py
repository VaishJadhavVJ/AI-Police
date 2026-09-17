import pytest

from app import validate_signup, create_app


@pytest.fixture
def client():
    return create_app().test_client()


class TestValidateSignup:
    def test_exact_8_char_password_is_accepted(self):
        """Regression test: 8 chars meets 'at least 8' and must not error."""
        errors = validate_signup({"email": "a@b.com", "password": "12345678"})
        assert errors == []

    def test_7_char_password_is_rejected(self):
        errors = validate_signup({"email": "a@b.com", "password": "1234567"})
        assert "password must be at least 8 characters" in errors

    def test_longer_password_accepted(self):
        errors = validate_signup({"email": "a@b.com", "password": "abcdefghij"})
        assert errors == []

    def test_missing_password_rejected(self):
        errors = validate_signup({"email": "a@b.com"})
        assert "password must be at least 8 characters" in errors

    def test_invalid_email_still_rejected(self):
        errors = validate_signup({"email": "nope", "password": "12345678"})
        assert "invalid email" in errors


class TestSignupEndpoint:
    def test_signup_8_char_password_returns_201(self, client):
        resp = client.post(
            "/signup", json={"email": "user@example.com", "password": "12345678"}
        )
        assert resp.status_code == 201
        assert resp.get_json() == {"message": "signup accepted"}

    def test_signup_7_char_password_returns_400(self, client):
        resp = client.post(
            "/signup", json={"email": "user@example.com", "password": "1234567"}
        )
        assert resp.status_code == 400
        assert resp.get_json()["errors"] == [
            "password must be at least 8 characters"
        ]
