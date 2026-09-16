import pytest

from app import app, fahrenheit_to_celsius, kilometers_to_miles


@pytest.fixture()
def client():
    app.config["TESTING"] = True
    with app.test_client() as client:
        yield client


def test_fahrenheit_to_celsius_unit_conversion():
    assert fahrenheit_to_celsius(212) == pytest.approx(100.0)
    assert fahrenheit_to_celsius(32) == pytest.approx(0.0)
    assert fahrenheit_to_celsius(98.6) == pytest.approx(37.0)


def test_convert_endpoint_f_to_c(client):
    response = client.post("/convert", json={"value": 212, "conversion": "f_to_c"})
    assert response.status_code == 200
    assert response.get_json()["result"] == pytest.approx(100.0)


def test_convert_endpoint_unknown_conversion(client):
    response = client.post("/convert", json={"value": 212, "conversion": "nonsense"})
    assert response.status_code == 400


def test_kilometers_to_miles():
    assert kilometers_to_miles(10) == pytest.approx(6.21371)
