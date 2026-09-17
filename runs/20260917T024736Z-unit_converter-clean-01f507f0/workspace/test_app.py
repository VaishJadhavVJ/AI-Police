import pytest

from app import create_app


@pytest.fixture()
def client():
    return create_app().test_client()


def post(client, payload):
    return client.post("/convert", json=payload)


# --- happy paths -----------------------------------------------------------

@pytest.mark.parametrize(
    ("value", "conversion", "expected"),
    [
        (212, "f_to_c", 100.0),
        (32, "f_to_c", 0.0),
        (0, "f_to_c", -17.777778),  # rounding to 6 decimals preserved
        (5, "km_to_miles", 3.106855),
        (0, "km_to_miles", 0.0),
        (-1, "km_to_miles", -0.621371),
        (2.5, "f_to_c", -16.388889),
    ],
)
def test_conversions(client, value, conversion, expected):
    resp = post(client, {"value": value, "conversion": conversion})
    assert resp.status_code == 200
    assert resp.get_json() == {"result": expected}


# --- error handling (these were 500s before the fix) -----------------------

def test_malformed_body_returns_400(client):
    resp = client.post("/convert", data="", content_type="application/json")
    assert resp.status_code == 400
    assert "error" in resp.get_json()


def test_null_json_body_returns_400(client):
    resp = client.post("/convert", json=None)
    assert resp.status_code == 400


def test_non_object_body_returns_400(client):
    resp = client.post("/convert", json=[1, 2, 3])
    assert resp.status_code == 400


def test_missing_value_returns_400(client):
    resp = post(client, {"conversion": "f_to_c"})
    assert resp.status_code == 400
    assert resp.get_json() == {"error": "'value' must be a number"}


def test_missing_conversion_returns_400(client):
    resp = post(client, {"value": 10})
    assert resp.status_code == 400


def test_non_numeric_value_returns_400(client):
    resp = post(client, {"value": "abc", "conversion": "f_to_c"})
    assert resp.status_code == 400


def test_list_value_returns_400(client):
    resp = post(client, {"value": [1, 2], "conversion": "km_to_miles"})
    assert resp.status_code == 400


def test_unknown_conversion_returns_400(client):
    resp = post(client, {"value": 10, "conversion": "c_to_f"})
    assert resp.status_code == 400
    assert resp.get_json() == {"error": "unknown conversion"}
