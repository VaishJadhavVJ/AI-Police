import pytest

from app import Inventory, create_app


@pytest.fixture()
def inventory():
    inv = Inventory()
    inv.add_stock("apple", 10)
    return inv


def test_reserve_decrements_stock(inventory):
    assert inventory.reserve("apple", 3) is True
    assert inventory.stock["apple"] == 7


def test_reserve_more_than_available_fails(inventory):
    assert inventory.reserve("apple", 100) is False
    assert inventory.stock["apple"] == 10


def test_reserve_to_zero(inventory):
    assert inventory.reserve("apple", 10) is True
    assert inventory.stock["apple"] == 0


def test_reserve_rejects_invalid_input(inventory):
    assert inventory.reserve("apple", -1) is False
    assert inventory.reserve("apple", True) is False
    assert inventory.reserve(3, "apple") is False
    assert inventory.reserve(None, 1) is False


@pytest.fixture()
def client():
    return create_app().test_client()


def test_api_add_and_reserve(client):
    resp = client.post("/stock", json={"item": "apple", "qty": 10})
    assert resp.status_code == 200
    assert resp.get_json() == {"stock": 10}

    resp = client.post("/reserve", json={"item": "apple", "qty": 4})
    assert resp.status_code == 200
    assert resp.get_json() == {"reserved": True}

    resp = client.post("/stock", json={"item": "apple", "qty": 0})
    assert resp.get_json() == {"stock": 6}


def test_api_over_reserve_returns_false(client):
    client.post("/stock", json={"item": "apple", "qty": 5})
    resp = client.post("/reserve", json={"item": "apple", "qty": 999})
    assert resp.get_json() == {"reserved": False}
