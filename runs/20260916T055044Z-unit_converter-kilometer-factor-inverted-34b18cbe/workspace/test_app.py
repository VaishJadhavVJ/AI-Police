import math

import pytest

from app import app, kilometers_to_miles, fahrenheit_to_celsius


@pytest.fixture()
def client():
    app.config["TESTING"] = True
    with app.test_client() as client:
        yield client


def test_kilometers_to_miles_unit():
    # 1 km should be ~0.621371 miles
    assert math.isclose(kilometers_to_miles(1), 0.621371, rel_tol=1e-9)


def test_kilometers_to_miles_reported_case():
    # Reported bug: 10 km returned ~16. Correct answer is ~6.2137.
    assert math.isclose(kilometers_to_miles(10), 6.21371, rel_tol=1e-9)


def test_convert_endpoint_km_to_miles(client):
    resp = client.post("/convert", json={"value": 10, "conversion": "km_to_miles"})
    assert resp.status_code == 200
    assert resp.get_json()["result"] == pytest.approx(6.21371, abs=1e-6)


def test_convert_endpoint_f_to_c(client):
    resp = client.post("/convert", json={"value": 212, "conversion": "f_to_c"})
    assert resp.status_code == 200
    assert resp.get_json()["result"] == pytest.approx(100.0, abs=1e-6)


def test_convert_endpoint_unknown_conversion(client):
    resp = client.post("/convert", json={"value": 1, "conversion": "bogus"})
    assert resp.status_code == 400
