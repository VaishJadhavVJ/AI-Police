import pytest

from app import calculate_total, create_app


@pytest.fixture
def client():
    app = create_app()
    app.config["TESTING"] = True
    with app.test_client() as client:
        yield client


def cart(price, qty=1):
    return [{"name": "widget", "price": price, "qty": qty}]


def test_no_coupon_tax_on_full_subtotal():
    # $100 cart, no coupon -> 8% tax on $100 = $108.00
    assert calculate_total(cart(100.0)) == 108.0


def test_coupon_applied_before_tax():
    # $100 cart with SAVE10 -> $10 off first, then 8% tax on $90 = $97.20
    assert calculate_total(cart(100.0), coupon="SAVE10") == 97.2


def test_coupon_threshold_uses_pretax_subtotal():
    # $50 cart qualifies for the discount: ($50 - $10) * 1.08 = $43.20
    assert calculate_total(cart(50.0), coupon="SAVE10") == 43.2


def test_coupon_below_threshold_no_discount():
    # $49.99 cart does not qualify -> tax on the full amount
    assert calculate_total(cart(49.99), coupon="SAVE10") == 53.99


def test_unknown_coupon_rejected():
    with pytest.raises(ValueError):
        calculate_total(cart(100.0), coupon="BOGUS")


def test_invalid_qty_rejected():
    with pytest.raises(ValueError):
        calculate_total([{"name": "widget", "price": 10.0, "qty": 0}])


def test_negative_price_rejected():
    with pytest.raises(ValueError):
        calculate_total([{"name": "widget", "price": -1.0, "qty": 1}])


def test_endpoint_total_with_coupon(client):
    resp = client.post("/total", json={"items": cart(100.0), "coupon": "SAVE10"})
    assert resp.status_code == 200
    assert resp.get_json()["total"] == 97.2


def test_endpoint_invalid_coupon(client):
    resp = client.post("/total", json={"items": cart(100.0), "coupon": "BOGUS"})
    assert resp.status_code == 400
    assert resp.get_json() == {"error": "invalid cart"}
