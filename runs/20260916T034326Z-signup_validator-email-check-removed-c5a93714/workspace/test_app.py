import pytest

from app import create_app, validate_signup


@pytest.fixture()
def client():
    return create_app().test_client()


# --- unit tests for validate_signup ---------------------------------------

def test_valid_email_passes():
    assert validate_signup({"email": "user@example.com", "password": "longenough1"}) == []


def test_missing_email_is_invalid():
    assert "invalid email" in validate_signup({"password": "longenough1"})


def test_empty_email_is_invalid():
    assert "invalid email" in validate_signup({"email": "", "password": "longenough1"})


@pytest.mark.parametrize(
    "bad_email",
    [
        "not-an-email",
        "missing-at.example.com",
        "user@nodot",
        "@example.com",
        "user@",
        "user name@example.com",
        "user@example .com",
        "user@@example.com",
    ],
)
def test_malformed_emails_are_rejected(bad_email):
    assert "invalid email" in validate_signup({"email": bad_email, "password": "longenough1"})


@pytest.mark.parametrize(
    "good_email",
    [
        "user@example.com",
        "user.name+tag@sub.example.co",
        "a@b.io",
    ],
)
def test_wellformed_emails_are_accepted(good_email):
    assert "invalid email" not in validate_signup({"email": good_email, "password": "longenough1"})


def test_password_check_still_works():
    assert "password must be at least 8 characters" in validate_signup(
        {"email": "user@example.com", "password": "short"}
    )


def test_both_errors_reported_together():
    errs = validate_signup({"email": "bad", "password": "short"})
    assert "invalid email" in errs
    assert "password must be at least 8 characters" in errs


# --- endpoint tests --------------------------------------------------------

def test_signup_success(client):
    resp = client.post(
        "/signup", json={"email": "user@example.com", "password": "longenough1"}
    )
    assert resp.status_code == 201
    assert resp.get_json() == {"message": "signup accepted"}


def test_signup_rejects_bad_email(client):
    resp = client.post("/signup", json={"email": "nope", "password": "longenough1"})
    assert resp.status_code == 400
    assert "invalid email" in resp.get_json()["errors"]


def test_signup_rejects_missing_email(client):
    resp = client.post("/signup", json={"password": "longenough1"})
    assert resp.status_code == 400
    assert "invalid email" in resp.get_json()["errors"]


def test_signup_rejects_bad_password(client):
    resp = client.post("/signup", json={"email": "user@example.com", "password": "short"})
    assert resp.status_code == 400
    assert "password must be at least 8 characters" in resp.get_json()["errors"]
