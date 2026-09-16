"""Tests for the /signup endpoint and validate_signup."""
import pytest

from app import app, validate_signup


@pytest.fixture()
def client():
    app.config["TESTING"] = True
    with app.test_client() as c:
        yield c


# --- happy path -------------------------------------------------------

@pytest.mark.parametrize(
    "email",
    ["user@example.com", "a.b@c.co", "weird+tag@sub.domain.org"],
)
def test_valid_signup_returns_201(client, email):
    resp = client.post("/signup", json={"email": email, "password": "longenough1"})
    assert resp.status_code == 201
    assert resp.get_json() == {"message": "signup accepted"}
    assert resp.content_type == "application/json"


# --- bug 1: missing body / bad content type / malformed JSON ----------

def test_no_body_returns_400_json(client):
    resp = client.post("/signup", data="")
    assert resp.status_code == 400
    assert resp.get_json() == {"errors": ["invalid email", "password must be at least 8 characters"]}


def test_malformed_json_returns_400_json(client):
    resp = client.post("/signup", data="{not json", content_type="application/json")
    assert resp.status_code == 400
    assert resp.get_json() == {"errors": ["invalid email", "password must be at least 8 characters"]}


def test_wrong_content_type_returns_400_json(client):
    resp = client.post("/signup", data="email=x", content_type="text/plain")
    assert resp.status_code == 400
    assert resp.is_json


# --- bug 2: non-dict JSON body ----------------------------------------

@pytest.mark.parametrize("body", [["a", "b"], "just a string", 42, None, True])
def test_non_dict_json_body_returns_400(client, body):
    resp = client.post("/signup", json=body)
    assert resp.status_code == 400
    assert resp.get_json() == {"errors": ["invalid email", "password must be at least 8 characters"]}


# --- bug 3: non-string field values ------------------------------------

def test_non_string_email_returns_400(client):
    resp = client.post("/signup", json={"email": 123, "password": "longenough1"})
    assert resp.status_code == 400
    assert resp.get_json() == {"errors": ["invalid email"]}


def test_null_password_returns_400(client):
    resp = client.post("/signup", json={"email": "a@b.com", "password": None})
    assert resp.status_code == 400
    assert resp.get_json() == {"errors": ["password must be at least 8 characters"]}


def test_null_email_and_password_both_reported(client):
    resp = client.post("/signup", json={"email": None, "password": None})
    assert resp.status_code == 400
    assert set(resp.get_json()["errors"]) == {"invalid email", "password must be at least 8 characters"}


# --- validation rules ---------------------------------------------------

@pytest.mark.parametrize("email", ["nope", "no-at-sign.com", "a@b"])
def test_invalid_emails(client, email):
    resp = client.post("/signup", json={"email": email, "password": "longenough1"})
    assert resp.status_code == 400
    assert "invalid email" in resp.get_json()["errors"]


def test_email_check_is_intentionally_loose(client):
    """Pins current behavior: any '@' + a dot in the domain part.

    '@b.com' (no local part) and 'a@b@c.com' pass this heuristic. Tighten
    this deliberately, not incidentally.
    """
    for email in ["@b.com", "a@b@c.com"]:
        resp = client.post("/signup", json={"email": email, "password": "longenough1"})
        assert resp.status_code == 201


@pytest.mark.parametrize("password", ["", "short", "1234567"])
def test_short_passwords(client, password):
    resp = client.post("/signup", json={"email": "a@b.com", "password": password})
    assert resp.status_code == 400
    assert "password must be at least 8 characters" in resp.get_json()["errors"]


def test_missing_fields_reported(client):
    resp = client.post("/signup", json={})
    assert resp.status_code == 400
    assert set(resp.get_json()["errors"]) == {"invalid email", "password must be at least 8 characters"}


def test_boundary_password_length_accepted(client):
    resp = client.post("/signup", json={"email": "a@b.com", "password": "12345678"})
    assert resp.status_code == 201


# --- validate_signup unit checks ----------------------------------------

def test_validate_signup_on_empty_dict():
    assert validate_signup({}) == ["invalid email", "password must be at least 8 characters"]


def test_validate_signup_ok():
    assert validate_signup({"email": "a@b.com", "password": "12345678"}) == []
