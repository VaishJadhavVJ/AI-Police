"""Tests for the inventory service."""

import pytest

from app import create_app, Inventory


@pytest.fixture()
def client():
    return create_app().test_client()


# ---------------------------------------------------------------- /stock


def test_add_stock_happy_path(client):
    r = client.post("/stock", json={"item": "widget", "qty": 5})
    assert r.status_code == 200
    assert r.get_json() == {"stock": 5}


def test_add_stock_accumulates(client):
    client.post("/stock", json={"item": "widget", "qty": 5})
    r = client.post("/stock", json={"item": "widget", "qty": 3})
    assert r.status_code == 200
    assert r.get_json() == {"stock": 8}


def test_add_stock_zero_qty_ok(client):
    r = client.post("/stock", json={"item": "widget", "qty": 0})
    assert r.status_code == 200
    assert r.get_json() == {"stock": 0}


@pytest.mark.parametrize(
    "payload",
    [
        {"item": "widget", "qty": -1},   # negative
        {"item": "widget", "qty": 2.5},  # float
        {"item": "widget", "qty": "3"},  # numeric string
        {"item": "widget", "qty": True},  # bool is not a valid quantity
        {"item": "widget"},              # missing qty
        {"qty": 3},                      # missing item
        {},                              # missing both
        {"item": 42, "qty": 3},          # non-string item key
    ],
)
def test_add_stock_invalid_input(client, payload):
    r = client.post("/stock", json=payload)
    assert r.status_code == 400
    assert "error" in r.get_json()


def test_add_stock_non_object_body(client):
    for body in ("null", "[1, 2]", '"str"'):
        r = client.post("/stock", data=body, content_type="application/json")
        assert r.status_code == 400


# ---------------------------------------------------------------- /reserve
# 400 = malformed request (body/keys unreadable). A well-formed request that
# simply cannot be fulfilled (unknown item, insufficient/negative/invalid qty)
# stays a 200 with reserved=false, per the model's contract.


def test_reserve_happy_path(client):
    client.post("/stock", json={"item": "widget", "qty": 5})
    r = client.post("/reserve", json={"item": "widget", "qty": 3})
    assert r.status_code == 200
    assert r.get_json() == {"reserved": True}


def test_reserve_decrements_stock(client):
    client.post("/stock", json={"item": "widget", "qty": 5})
    client.post("/reserve", json={"item": "widget", "qty": 3})
    r = client.post("/reserve", json={"item": "widget", "qty": 2})
    assert r.get_json() == {"reserved": True}
    # only 0 left now
    assert client.post("/reserve", json={"item": "widget", "qty": 1}).get_json() == {
        "reserved": False
    }


def test_reserve_insufficient_stock_is_false_not_error(client):
    client.post("/stock", json={"item": "widget", "qty": 2})
    r = client.post("/reserve", json={"item": "widget", "qty": 3})
    assert r.status_code == 200
    assert r.get_json() == {"reserved": False}


def test_reserve_unknown_item_is_false_not_error(client):
    r = client.post("/reserve", json={"item": "ghost", "qty": 1})
    assert r.status_code == 200
    assert r.get_json() == {"reserved": False}


def test_reserve_non_string_item_is_false_not_error(client):
    # Model contract: non-string items can never be reserved -> False.
    r = client.post("/reserve", json={"item": 42, "qty": 1})
    assert r.status_code == 200
    assert r.get_json() == {"reserved": False}


def test_reserve_rejects_bool_qty_without_touching_stock(client):
    client.post("/stock", json={"item": "widget", "qty": 5})
    r = client.post("/reserve", json={"item": "widget", "qty": True})
    assert r.status_code == 200
    assert r.get_json() == {"reserved": False}
    # stock untouched by the bool attempt
    assert client.post("/reserve", json={"item": "widget", "qty": 5}).get_json() == {
        "reserved": True
    }


def test_reserve_negative_qty_is_false_not_error(client):
    client.post("/stock", json={"item": "widget", "qty": 5})
    r = client.post("/reserve", json={"item": "widget", "qty": -2})
    assert r.status_code == 200
    assert r.get_json() == {"reserved": False}


@pytest.mark.parametrize(
    "payload",
    [
        {"item": "widget"},  # missing qty
        {"qty": 1},          # missing item
        {},                  # missing both
    ],
)
def test_reserve_missing_keys_returns_400_not_500(client, payload):
    r = client.post("/reserve", json=payload)
    assert r.status_code == 400
    assert "error" in r.get_json()


@pytest.mark.parametrize("body", ["null", "[1, 2]", '"str"', "{"])
def test_reserve_non_object_or_malformed_body_returns_400_not_500(client, body):
    r = client.post("/reserve", data=body, content_type="application/json")
    assert r.status_code == 400


# ---------------------------------------------------------------- model


def test_model_rejects_bad_input_directly():
    inv = Inventory()
    with pytest.raises(ValueError):
        inv.add_stock("x", -1)
    with pytest.raises(ValueError):
        inv.add_stock("x", True)
    with pytest.raises(ValueError):
        inv.add_stock(42, 1)  # non-string item
    assert inv.reserve("x", True) is False
    assert inv.reserve("x", "1") is False
    inv.add_stock("x", 2)
    assert inv.reserve("x", 3) is False
    assert inv.reserve("x", 2) is True
    assert inv.stock["x"] == 0
