import pytest

from app import create_app


@pytest.fixture()
def client():
    return create_app().test_client()


def post_signup(client, payload):
    return client.post("/signup", json=payload)


@pytest.mark.parametrize(
    "email",
    [
        "not-an-email",        # reported by users
        "",
        "foo@",
        "@example.com",
        "foo@example",         # no dot in domain
        "foo bar@example.com", # space
        "foo@.com",            # empty domain label
        "foo@example..com",    # consecutive dots in domain
        ".foo@example.com",    # leading dot in local part
        "foo.@example.com",    # trailing dot in local part
        None,
    ],
)
def test_invalid_emails_are_rejected(client, email):
    resp = post_signup(client, {"email": email, "password": "longenough1"})
    assert resp.status_code == 400, f"{email!r} should be rejected"
    assert "invalid email" in resp.get_json()["errors"]


def test_missing_email_is_rejected(client):
    resp = post_signup(client, {"password": "longenough1"})
    assert resp.status_code == 400
    assert "invalid email" in resp.get_json()["errors"]


@pytest.mark.parametrize(
    "email",
    [
        "user@example.com",
        "user.name+tag@sub.example.co",
        "a@b.co",
        "UPPER.case@Example.COM",
    ],
)
def test_valid_emails_are_accepted(client, email):
    resp = post_signup(client, {"email": email, "password": "longenough1"})
    assert resp.status_code == 201, f"{email!r} should be accepted"


def test_short_password_still_rejected(client):
    resp = post_signup(client, {"email": "user@example.com", "password": "short"})
    assert resp.status_code == 400
    assert "password must be at least 8 characters" in resp.get_json()["errors"]
