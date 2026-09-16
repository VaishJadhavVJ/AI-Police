import pytest

from app import TAX_RATE, calculate_total, create_app


# ---------- calculate_total ----------

def test_no_items_no_coupon():
    assert calculate_total([]) == 0.0


def test_simple_subtotal():
    assert calculate_total([{"price": 10.0, "qty": 3}]) == pytest.approx(30.0 * (1 + TAX_RATE))


def test_multiple_items():
    total = calculate_total([{"price": 10.0, "qty": 2}, {"price": 5.0, "qty": 1}])
    assert total == round(25.0 * (1 + TAX_RATE), 2)


def test_discount_before_tax():
    # 100 - 10 coupon = 90 -> tax on 90
    assert calculate_total([{"price": 100.0, "qty": 1}], coupon="SAVE10") == 97.2


def test_coupon_below_threshold_no_discount():
    # 49.99 is under the 50 minimum: no discount
    assert calculate_total([{"price": 49.99, "qty": 1}], coupon="SAVE10") == round(49.99 * (1 + TAX_RATE), 2)


def test_exact_threshold_gets_discount():
    assert calculate_total([{"price": 50.0, "qty": 1}], coupon="SAVE10") == 43.2


def test_unknown_coupon():
    with pytest.raises(ValueError):
        calculate_total([{"price": 10.0, "qty": 1}], coupon="BOGUS")


def test_unknown_coupon_below_threshold_still_raises():
    with pytest.raises(ValueError):
        calculate_total([{"price": 1.0, "qty": 1}], coupon="BOGUS")


def test_invalid_qty_zero():
    with pytest.raises(ValueError):
        calculate_total([{"price": 10.0, "qty": 0}])


def test_invalid_qty_bool():
    with pytest.raises(ValueError):
        calculate_total([{"price": 10.0, "qty": True}])


def test_negative_price():
    with pytest.raises(ValueError):
        calculate_total([{"price": -1.0, "qty": 1}])


def test_rounding_two_decimals():
    assert calculate_total([{"price": 10.0, "qty": 3}]) == round(30.0 * (1 + TAX_RATE), 2)


# ---------- HTTP layer ----------

@pytest.fixture()
def client():
    return create_app().test_client()


def test_endpoint_ok(client):
    resp = client.post("/total", json={"items": [{"price": 100.0, "qty": 1}], "coupon": "SAVE10"})
    assert resp.status_code == 200
    assert resp.get_json() == {"total": 97.2}


def test_endpoint_bad_json(client):
    resp = client.post("/total", json={"items": [{"price": 1.0, "qty": 0}]})
    assert resp.status_code == 400
    assert "error" in resp.get_json()


def test_endpoint_missing_items(client):
    resp = client.post("/total", json={"coupon": "SAVE10"})
    assert resp.status_code == 400
