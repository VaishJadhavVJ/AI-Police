import pytest

from app import create_app, validate_email, validate_signup


@pytest.fixture()
def client():
    return create_app().test_client()


# ---------------------------------------------------------------- unit: validate_email
@pytest.mark.parametrize(
    "email",
    [
        "user@example.com",
        "user.name+tag@sub.example.co.uk",
        "a_b-c@d-e.org",
        "x@y.io",
    ],
)
def test_valid_emails(email):
    assert validate_email(email)


@pytest.mark.parametrize(
    "email",
    [
        "not-an-email",        # the reported bug: no '@' at all
        "",
        "   ",
        "user",
        "user@",
        "@example.com",
        "user@domain",         # no TLD
        "user @example.com",   # space
        " user@example.com",   # leading whitespace
        "user@example.com ",   # trailing whitespace
        "user@@example.com",   # two '@'
        "us er@example.com",
        ".user@example.com",   # leading dot in local part
        "user.@example.com",   # trailing dot in local part
        "us..er@example.com",  # consecutive dots
        "user@-example.com",   # label starts with hyphen
        "user@example-.com",   # label ends with hyphen
        "user@example.c",      # TLD too short
        "user@exa_mple.com",   # underscore not allowed in domain
        "user@exam ple.com",   # space in domain
    ],
)
def test_invalid_emails(email):
    assert not validate_email(email)


# ---------------------------------------------------------------- unit: validate_signup
def test_signup_rejects_bad_email():
    errors = validate_signup({"email": "not-an-email", "password": "longenough"})
    assert "invalid email" in errors


def test_signup_rejects_short_password_only():
    errors = validate_signup({"email": "user@example.com", "password": "short"})
    assert errors == ["password must be at least 8 characters"]


def test_signup_accepts_good_data():
    assert validate_signup({"email": "user@example.com", "password": "longenough"}) == []


# ---------------------------------------------------------------- HTTP behaviour
def test_endpoint_rejects_invalid_email(client):
    resp = client.post("/signup", json={"email": "not-an-email", "password": "longenough"})
    assert resp.status_code == 400
    assert "invalid email" in resp.get_json()["errors"]


def test_endpoint_accepts_valid_email(client):
    resp = client.post("/signup", json={"email": "user@example.com", "password": "longenough"})
    assert resp.status_code == 201
    assert resp.get_json() == {"message": "signup accepted"}
