import json

import pytest

from app import app, calculate_total


# ---- direct unit tests on calculate_total ----

def test_zero_qty_rejected():
    with pytest.raises(ValueError):
        calculate_total([{"qty": 0, "price": 5.0}])


def test_negative_qty_rejected():
    with pytest.raises(ValueError):
        calculate_total([{"qty": -3, "price": 5.0}])


def test_negative_price_still_rejected():
    with pytest.raises(ValueError):
        calculate_total([{"qty": 1, "price": -1.0}])


def test_valid_cart_still_works():
    # 2 * 10.00 with 8% tax = 21.60
    assert calculate_total([{"qty": 2, "price": 10.0}]) == 21.60


def test_coupon_still_works():
    # subtotal 100, discount 10 -> 90 * 1.08 = 97.20
    assert calculate_total([{"qty": 10, "price": 10.0}], coupon="SAVE10") == 97.20


def test_empty_cart_ok():
    assert calculate_total([]) == 0.0


# ---- end-to-end tests through the Flask endpoint ----

def _post(client, items, coupon=None):
    body = {"items": items}
    if coupon is not None:
        body["coupon"] = coupon
    return client.post("/total", data=json.dumps(body), content_type="application/json")


@pytest.fixture
def client():
    return app.test_client()


def test_api_accepts_valid_order(client):
    resp = _post(client, [{"qty": 2, "price": 10.0}])
    assert resp.status_code == 200
    assert resp.get_json()["total"] == 21.60


@pytest.mark.parametrize("qty", [0, -1, -100])
def test_api_rejects_nonpositive_qty(client, qty):
    resp = _post(client, [{"qty": qty, "price": 10.0}])
    assert resp.status_code == 400
    assert resp.get_json()["error"] == "invalid cart"


def test_api_rejects_bad_coupon(client):
    resp = _post(client, [{"qty": 1, "price": 10.0}], coupon="BOGUS")
    assert resp.status_code == 400
