import pytest

from app import Inventory, create_app


@pytest.fixture
def client():
    return create_app().test_client()


def test_add_stock_accepts_positive_and_zero():
    inv = Inventory()
    inv.add_stock("widget", 10)
    inv.add_stock("widget", 0)
    inv.add_stock("widget", 5)
    assert inv.stock["widget"] == 15


def test_add_stock_rejects_negative_qty():
    inv = Inventory()
    with pytest.raises(ValueError):
        inv.add_stock("widget", -3)
    assert inv.stock.get("widget", 0) == 0


def test_add_stock_negative_does_not_lower_existing_count():
    inv = Inventory()
    inv.add_stock("widget", 10)
    with pytest.raises(ValueError):
        inv.add_stock("widget", -3)
    assert inv.stock["widget"] == 10


def test_add_stock_rejects_negative_float_qty():
    inv = Inventory()
    with pytest.raises(ValueError):
        inv.add_stock("widget", -0.5)
    assert inv.stock.get("widget", 0) == 0


def test_http_post_stock_negative_returns_400(client):
    resp = client.post("/stock", json={"item": "gizmo", "qty": -5})
    assert resp.status_code == 400
    assert "error" in resp.get_json()


def test_http_post_stock_negative_does_not_change_stock(client):
    client.post("/stock", json={"item": "gizmo", "qty": 7})
    client.post("/stock", json={"item": "gizmo", "qty": -5})
    resp = client.post("/stock", json={"item": "gizmo", "qty": 3})
    assert resp.status_code == 200
    assert resp.get_json()["stock"] == 10  # 7 + 3, the -5 was rejected


def test_http_post_stock_positive_still_works(client):
    resp = client.post("/stock", json={"item": "gizmo", "qty": 5})
    assert resp.status_code == 200
    assert resp.get_json() == {"stock": 5}


def test_reserve_regression(client):
    client.post("/stock", json={"item": "bolt", "qty": 4})
    assert client.post("/reserve", json={"item": "bolt", "qty": 3}).get_json() == {"reserved": True}
    assert client.post("/reserve", json={"item": "bolt", "qty": 3}).get_json() == {"reserved": False}
    assert client.post("/reserve", json={"item": "bolt", "qty": -1}).get_json() == {"reserved": False}
