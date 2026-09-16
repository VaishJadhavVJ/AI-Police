"""Regression tests for calculate_total and the /total endpoint.

Key invariant under test: the coupon discount is applied to the pre-tax
subtotal, and tax is computed on the discounted amount.
"""

import math

import pytest

from app import TAX_RATE, calculate_total, create_app


@pytest.fixture
def client():
    return create_app().test_client()


def close(a, b):
    return math.isclose(a, b, abs_tol=1e-9)


# ---------------------------------------------------------------- coupon order

def test_discount_applied_before_tax():
    """$60 cart with SAVE10: tax on (60 - 10), not on 60."""
    # before-tax discount: (60 - 10) * 1.08 = 54.00
    # after-tax discount (the bug): 60 * 1.08 - 10 = 54.80
    assert calculate_total([{"qty": 3, "price": 20.0}], coupon="SAVE10") == 54.00


def test_no_coupon_taxes_full_subtotal():
    assert close(calculate_total([{"qty": 3, "price": 20.0}]), round(60.0 * (1 + TAX_RATE), 2))


def test_tax_is_on_discounted_amount_not_undiscounted():
    """$100 cart with SAVE10: (100 - 10) * 1.08 = 97.20, not 100 * 1.08 - 10 = 98.00."""
    assert calculate_total([{"qty": 4, "price": 25.0}], coupon="SAVE10") == 97.20


# ------------------------------------------------------------- coupon rules

def test_coupon_below_threshold_gets_no_discount():
    # $40 subtotal: coupon does not apply, tax on full $40.
    assert close(calculate_total([{"qty": 2, "price": 20.0}], coupon="SAVE10"),
                 round(40.0 * (1 + TAX_RATE), 2))


def test_coupon_at_exact_threshold_applies():
    # $50 subtotal: qualifies, (50 - 10) * 1.08 = 43.20
    assert close(calculate_total([{"qty": 5, "price": 10.0}], coupon="SAVE10"), 43.20)


def test_unknown_coupon_raises():
    with pytest.raises(ValueError):
        calculate_total([{"qty": 1, "price": 10.0}], coupon="BOGUS")


# ------------------------------------------------------------- validation

def test_bad_qty_raises():
    for bad in (0, -1, 1.5, "2", True):
        with pytest.raises(ValueError):
            calculate_total([{"qty": bad, "price": 10.0}])


def test_negative_price_raises():
    with pytest.raises(ValueError):
        calculate_total([{"qty": 1, "price": -5.0}])


# ------------------------------------------------------------- HTTP endpoint

def test_endpoint_discount_before_tax(client):
    resp = client.post("/total", json={"items": [{"qty": 3, "price": 20.0}],
                                       "coupon": "SAVE10"})
    assert resp.status_code == 200
    assert resp.get_json()["total"] == 54.00


def test_endpoint_no_coupon(client):
    resp = client.post("/total", json={"items": [{"qty": 3, "price": 20.0}]})
    assert resp.status_code == 200
    assert close(resp.get_json()["total"], 64.80)


def test_endpoint_invalid_body_returns_400(client):
    assert client.post("/total", json={"coupon": "SAVE10"}).status_code == 400
    assert client.post("/total", json={"items": [{"qty": 0, "price": 10.0}]}).status_code == 400
    assert client.post("/total", data="not json",
                       content_type="application/json").status_code in (400, 415)


def test_endpoint_unknown_coupon_returns_400(client):
    resp = client.post("/total", json={"items": [{"qty": 1, "price": 10.0}],
                                       "coupon": "NOPE"})
    assert resp.status_code == 400
