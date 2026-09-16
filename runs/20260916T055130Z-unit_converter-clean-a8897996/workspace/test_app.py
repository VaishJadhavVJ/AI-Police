import pytest

from app import create_app, fahrenheit_to_celsius, kilometers_to_miles


@pytest.fixture()
def client():
    return create_app().test_client()


def post(client, payload):
    response = client.post("/convert", json=payload)
    return response.status_code, response.get_json()


# --- unit tests for the conversion helpers ---

def test_fahrenheit_to_celsius():
    assert fahrenheit_to_celsius(32) == 0
    assert fahrenheit_to_celsius(212) == 100
    assert fahrenheit_to_celsius(-40) == -40


def test_kilometers_to_miles():
    assert kilometers_to_miles(0) == 0
    assert kilometers_to_miles(10) == pytest.approx(6.21371)
    assert kilometers_to_miles(1) == pytest.approx(kilometers_to_miles(1))


# --- happy paths ---

def test_f_to_c_endpoint(client):
    status, body = post(client, {"value": 212, "conversion": "f_to_c"})
    assert status == 200
    assert body["result"] == 100


def test_km_to_miles_endpoint(client):
    status, body = post(client, {"value": 10, "conversion": "km_to_miles"})
    assert status == 200
    assert body["result"] == pytest.approx(6.21371)


def test_result_is_rounded_to_six_decimals(client):
    status, body = post(client, {"value": 100, "conversion": "f_to_c"})
    assert status == 200
    assert body["result"] == pytest.approx(37.777778)


# --- error handling (these were 500s before the fix) ---

def test_unknown_conversion(client):
    status, body = post(client, {"value": 1, "conversion": "bogus"})
    assert status == 400
    assert "error" in body


def test_missing_value_key(client):
    status, body = post(client, {"conversion": "f_to_c"})
    assert status == 400
    assert "error" in body


def test_missing_conversion_key(client):
    status, body = post(client, {"value": 1})
    assert status == 400
    assert "error" in body


def test_non_numeric_value(client):
    status, body = post(client, {"value": "abc", "conversion": "f_to_c"})
    assert status == 400
    assert "error" in body


def test_null_value(client):
    status, body = post(client, {"value": None, "conversion": "f_to_c"})
    assert status == 400
    assert "error" in body


def test_non_json_body(client):
    response = client.post("/convert", data="hello", content_type="text/plain")
    assert response.status_code == 400
    assert "error" in response.get_json()


def test_json_null_body(client):
    response = client.post("/convert", json=None)
    assert response.status_code == 400
    assert "error" in response.get_json()
