import pytest

from app import create_app, fahrenheit_to_celsius, kilometers_to_miles


@pytest.mark.parametrize(
    "fahrenheit, expected",
    [
        (32, 0),      # freezing point
        (212, 100),   # boiling point
        (98.6, 37),   # body temperature
        (-40, -40),   # point where scales meet
    ],
)
def test_fahrenheit_to_celsius(fahrenheit, expected):
    assert round(fahrenheit_to_celsius(fahrenheit), 6) == pytest.approx(expected, abs=1e-6)


def test_kelvin_to_miles_reference():
    assert round(kilometers_to_miles(10), 6) == 6.21371


@pytest.fixture()
def client():
    return create_app().test_client()


def test_endpoint_f_to_c(client):
    response = client.post("/convert", json={"value": 212, "conversion": "f_to_c"})
    assert response.status_code == 200
    assert response.get_json() == {"result": 100.0}


def test_endpoint_unknown_conversion(client):
    response = client.post("/convert", json={"value": 1, "conversion": "c_to_f"})
    assert response.status_code == 400
