import math

import pytest

from app import app, calculate_total


# --- Unit tests for calculate_total ---


def test_save10_discount_applied_before_tax():
    # $60 cart with SAVE10: (60 - 10) * 1.08 = 54.00
    # The old buggy code returned 60 * 1.08 - 10 = 54.80 (taxing the discount).
    assert calculate_total([{"qty": 1, "price": 60.0}], coupon="SAVE10") == 54.00


def test_save10_at_threshold():
    # $50 cart qualifies for the discount: (50 - 10) * 1.08 = 43.20
    assert calculate_total([{"qty": 1, "price": 50.0}], coupon="SAVE10") == 43.20


def test_save10_below_threshold_gets_no_discount():
    # $49.99 cart does not qualify; tax on full subtotal.
    assert calculate_total([{"qty": 1, "price": 49.99}], coupon="SAVE10") == 53.99


def test_no_coupon_unchanged():
    assert calculate_total([{"qty": 2, "price": 10.0}]) == 21.60


def test_coupon_none_unchanged():
    assert calculate_total([{"qty": 2, "price": 10.0}], coupon=None) == 21.60


def test_unknown_coupon_raises():
    with pytest.raises(ValueError):
        calculate_total([{"qty": 1, "price": 60.0}], coupon="SAVE50")


def test_discount_never_makes_total_negative():
    # $50 cart (discount 10, taxed base 40) is fine, but guard the math anyway.
    total = calculate_total([{"qty": 1, "price": 50.0}], coupon="SAVE10")
    assert total >= 0


def test_multiple_items_with_coupon():
    # 25 + 30 = 55 subtotal; (55 - 10) * 1.08 = 48.60
    assert (
        calculate_total(
            [{"qty": 1, "price": 25.0}, {"qty": 1, "price": 30.0}], coupon="SAVE10"
        )
        == 48.60
    )


# --- Validation behavior should be unaffected by the fix ---


def test_invalid_qty_raises():
    with pytest.raises(ValueError):
        calculate_total([{"qty": 0, "price": 10.0}])
    with pytest.raises(ValueError):
        calculate_total([{"qty": True, "price": 10.0}])
    with pytest.raises(ValueError):
        calculate_total([{"qty": 1.5, "price": 10.0}])


def test_negative_price_raises():
    with pytest.raises(ValueError):
        calculate_total([{"qty": 1, "price": -1.0}])


# --- API endpoint tests ---


@pytest.fixture
def client():
    app.config["TESTING"] = True
    with app.test_client() as client:
        yield client


def post_json(client, payload):
    return client.post("/total", json=payload)


def test_endpoint_with_save10(client):
    resp = post_json(client, {"items": [{"qty": 1, "price": 60.0}], "coupon": "SAVE10"})
    assert resp.status_code == 200
    assert resp.get_json()["total"] == 54.00


def test_endpoint_without_coupon(client):
    resp = post_json(client, {"items": [{"qty": 1, "price": 60.0}]})
    assert resp.status_code == 200
    assert resp.get_json()["total"] == 64.80


def test_endpoint_invalid_coupon(client):
    resp = post_json(client, {"items": [{"qty": 1, "price": 60.0}], "coupon": "X"})
    assert resp.status_code == 400
    assert resp.get_json() == {"error": "invalid cart"}


def test_endpoint_missing_items(client):
    resp = post_json(client, {"coupon": "SAVE10"})
    assert resp.status_code == 400
