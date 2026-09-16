import pytest

from app import TAX_RATE, calculate_total, create_app


@pytest.fixture
def client():
    return create_app().test_client()


def test_save10_applies_at_exactly_50():
    """Regression: exactly-$50 cart must qualify for SAVE10."""
    items = [{"qty": 5, "price": 10.00}]
    # (50 - 10) * 1.08 = 43.20
    assert calculate_total(items, coupon="SAVE10") == 43.20


def test_save10_applies_at_exactly_50_despite_float_error():
    """Regression: 3*15.70 + 2*1.45 == 50.00 in decimal, but sums to
    49.99999999999999 as floats. Cent-rounding must still qualify it."""
    items = [{"qty": 3, "price": 15.70}, {"qty": 2, "price": 1.45}]
    assert sum(i["price"] * i["qty"] for i in items) < 50.0  # precondition
    assert calculate_total(items, coupon="SAVE10") == 43.20


def test_save10_applies_above_50():
    items = [{"qty": 1, "price": 50.01}]
    assert calculate_total(items, coupon="SAVE10") == round((50.01 - 10) * (1 + TAX_RATE), 2)


def test_save10_not_applied_below_50():
    items = [{"qty": 1, "price": 49.99}]
    assert calculate_total(items, coupon="SAVE10") == round(49.99 * (1 + TAX_RATE), 2)


def test_no_coupon():
    items = [{"qty": 5, "price": 10.00}]
    assert calculate_total(items) == round(50 * (1 + TAX_RATE), 2)


def test_unknown_coupon_raises():
    items = [{"qty": 5, "price": 10.00}]
    with pytest.raises(ValueError):
        calculate_total(items, coupon="BOGUS")


def test_invalid_qty_raises():
    with pytest.raises(ValueError):
        calculate_total([{"qty": 0, "price": 10.00}])
    with pytest.raises(ValueError):
        calculate_total([{"qty": True, "price": 10.00}])


def test_negative_price_raises():
    with pytest.raises(ValueError):
        calculate_total([{"qty": 1, "price": -5.00}])


def test_api_exact_50_with_save10(client):
    resp = client.post(
        "/total",
        json={"items": [{"qty": 4, "price": 12.50}], "coupon": "SAVE10"},
    )
    assert resp.status_code == 200
    assert resp.get_json()["total"] == 43.20


def test_api_exact_50_float_sensitive_with_save10(client):
    resp = client.post(
        "/total",
        json={
            "items": [{"qty": 3, "price": 15.70}, {"qty": 2, "price": 1.45}],
            "coupon": "SAVE10",
        },
    )
    assert resp.status_code == 200
    assert resp.get_json()["total"] == 43.20


def test_api_invalid_body(client):
    resp = client.post("/total", json={"items": [{"qty": -1, "price": 10.0}]})
    assert resp.status_code == 400
