"""Regression tests for app.py."""
import pytest

from app import create_app


@pytest.fixture()
def client():
    return create_app().test_client()


def post(client, path, data):
    return client.post(path, json=data) if data is not None else client.post(path)


# --- /stock happy paths ---------------------------------------------------

def test_add_stock_accumulates(client):
    r1 = client.post("/stock", json={"item": "apple", "qty": 10})
    r2 = client.post("/stock", json={"item": "apple", "qty": 5})
    assert r1.status_code == 200 and r1.get_json()["stock"] == 10
    assert r2.status_code == 200 and r2.get_json()["stock"] == 15


# --- /stock validation ------------------------------------------------------

@pytest.mark.parametrize(
    "payload",
    [
        {"item": "x", "qty": -1},
        {"item": "x", "qty": "5"},
        {"item": "x", "qty": True},
        {"item": "x", "qty": 1.5},
        {},
        {"item": "x"},
        {"qty": 5},
    ],
)
def test_add_stock_rejects_invalid(client, payload):
    r = client.post("/stock", json=payload)
    assert r.status_code == 400
    assert "error" in r.get_json()


def test_add_stock_rejects_non_dict_body(client):
    assert client.post("/stock", data="5", content_type="application/json").status_code == 400
    assert client.post("/stock", data="[1]", content_type="application/json").status_code == 400


def test_add_stock_rejects_missing_or_non_json_body(client):
    assert client.post("/stock").status_code == 400
    assert client.post("/stock", data="{not json", content_type="application/json").status_code == 400
    assert client.post("/stock", data="hello").status_code == 400


# --- /reserve happy paths ---------------------------------------------------

def test_reserve_success_and_insufficient_stock(client):
    client.post("/stock", json={"item": "apple", "qty": 10})
    r = client.post("/reserve", json={"item": "apple", "qty": 4})
    assert r.status_code == 200 and r.get_json() == {"reserved": True}

    r = client.post("/reserve", json={"item": "apple", "qty": 100})
    assert r.status_code == 200 and r.get_json() == {"reserved": False}


def test_reserve_unknown_item_returns_false_not_error(client):
    r = client.post("/reserve", json={"item": "ghost", "qty": 1})
    assert r.status_code == 200 and r.get_json() == {"reserved": False}


# --- /reserve malformed input: previously 500 crashes (the fixed bugs) ------

@pytest.mark.parametrize(
    "payload",
    [
        {"item": "x"},          # missing qty -> KeyError -> 500 before fix
        {"qty": 1},             # missing item -> KeyError -> 500 before fix
        {},                     # missing both
        [1, 2],                 # list body -> TypeError -> 500 before fix
        5,                      # scalar body -> TypeError -> 500 before fix
        "hello",                # string body -> TypeError -> 500 before fix
    ],
)
def test_reserve_never_500_on_malformed_input(client, payload):
    r = client.post("/reserve", json=payload)
    assert r.status_code == 400
    assert "error" in r.get_json()


def test_reserve_rejects_missing_or_non_json_body(client):
    assert client.post("/reserve").status_code == 400
    assert client.post("/reserve", data="{not json", content_type="application/json").status_code == 400
    assert client.post("/reserve", data="hello").status_code == 400


def test_reserve_rejects_invalid_qty(client):
    for qty in (-1, "5", True, 1.5, None):
        r = client.post("/reserve", json={"item": "x", "qty": qty})
        assert r.status_code == 200 and r.get_json() == {"reserved": False}


# --- concurrency ------------------------------------------------------------

def test_concurrent_reserves_ne_oversell():
    import threading

    app = create_app()
    c = app.test_client()
    c.post("/stock", json={"item": "widget", "qty": 100})
    results = []

    def worker():
        tc = app.test_client()
        for _ in range(50):
            r = tc.post("/reserve", json={"item": "widget", "qty": 1})
            results.append(r.get_json()["reserved"])

    threads = [threading.Thread(target=worker) for _ in range(10)]
    for t in threads:
        t.start()
    for t in threads:
        t.join()

    assert sum(results) == 100  # exactly 100 succeed, no oversell
    assert c.post("/reserve", json={"item": "widget", "qty": 1}).get_json() == {"reserved": False}
