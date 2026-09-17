import pytest
from app import fahrenheit_to_celsius, kilometers_to_miles, create_app


def test_fahrenheit_to_celsius():
    assert fahrenheit_to_celsius(212) == 100  # the reported case: boiling point
    assert fahrenheit_to_celsius(32) == 0     # freezing point
    assert fahrenheit_to_celsius(-40) == -40  # scales intersect


def test_fahrenheit_to_celsius_regular_values():
    assert fahrenheit_to_celsius(98.6) == 37.0
    assert fahrenheit_to_celsius(100) == pytest.approx(37.7778, abs=1e-4)


def test_kilometers_to_miles():
    assert kilometers_to_miles(10) == pytest.approx(6.21371, abs=1e-5)


def test_convert_endpoint():
    client = create_app().test_client()
    resp = client.post("/convert", json={"value": 212, "conversion": "f_to_c"})
    assert resp.status_code == 200
    assert resp.get_json()["result"] == 100

    resp = client.post("/convert", json={"value": 1, "conversion": "nonsense"})
    assert resp.status_code == 400
