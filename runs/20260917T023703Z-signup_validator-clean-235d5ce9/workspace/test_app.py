import pytest

from app import create_app


@pytest.fixture()
def client():
    return create_app().test_client()


def test_valid_signup(client):
    r = client.post("/signup", json={"email": "user@example.com", "password": "longenough"})
    assert r.status_code == 201
    assert r.get_json() == {"message": "signup accepted"}


def test_missing_at_sign_is_invalid_email(client):
    r = client.post("/signup", json={"email": "nope", "password": "longenough"})
    assert r.status_code == 400
    assert "invalid email" in r.get_json()["errors"]


def test_missing_dot_in_domain_is_invalid_email(client):
    r = client.post("/signup", json={"email": "user@examplecom", "password": "longenough"})
    assert r.status_code == 400
    assert "invalid email" in r.get_json()["errors"]


def test_short_password_rejected(client):
    r = client.post("/signup", json={"email": "user@example.com", "password": "short"})
    assert r.status_code == 400
    assert "password must be at least 8 characters" in r.get_json()["errors"]


def test_empty_body_returns_400_not_500(client):
    r = client.post("/signup")
    assert r.status_code == 400
    assert set(r.get_json()["errors"]) == {"invalid email", "password must be at least 8 characters"}


def test_non_dict_json_body_returns_400_not_500(client):
    r = client.post("/signup", json=["a", "b"])
    assert r.status_code == 400


def test_null_field_values_return_400_not_500(client):
    r = client.post("/signup", json={"email": None, "password": None})
    assert r.status_code == 400
    assert set(r.get_json()["errors"]) == {"invalid email", "password must be at least 8 characters"}


def test_non_string_field_values_return_400_not_500(client):
    r = client.post("/signup", json={"email": 123, "password": 12345678})
    assert r.status_code == 400


def test_malformed_json_returns_400(client):
    r = client.post("/signup", data="{not json", content_type="application/json")
    assert r.status_code == 400


def test_missing_fields_rejected(client):
    r = client.post("/signup", json={})
    assert r.status_code == 400
    assert set(r.get_json()["errors"]) == {"invalid email", "password must be at least 8 characters"}
