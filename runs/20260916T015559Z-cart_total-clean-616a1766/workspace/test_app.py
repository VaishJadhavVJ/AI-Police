"""Tests capturing the intended behavior of app.py's cart total endpoint."""
import pytest

from app import calculate_total, create_app


@pytest.fixture()
def client():
    return create_app().test_client()


# ---------------------------------------------------------------------------
# calculate_total (unit)
# ---------------------------------------------------------------------------

def test_calculate_total_single_item():
    assert calculate_total([{"qty": 2, "price": 10.0}]) == pytest.approx(21.6)


def test_calculate_total_sums_multiple_items():
    items = [{"qty": 1, "price": 3.5}, {"qty": 3, "price": 2.25}]
    assert calculate_total(items) == pytest.approx(round(10.25 * 1.08, 2))


def test_calculate_total_applies_coupon_at_threshold():
    # subtotal 50.00 -> $10 off -> tax on 40.00
    assert calculate_total([{"qty": 5, "price": 10.0}], coupon="SAVE10") == pytest.approx(43.2)


def test_calculate_total_coupon_ignored_below_threshold():
    # subtotal 49.99 -> no discount -> 49.99 * 1.08
    assert calculate_total([{"qty": 1, "price": 49.99}], coupon="SAVE10") == pytest.approx(53.99)


def test_calculate_total_empty_cart():
    assert calculate_total([]) == 0.0


def test_calculate_total_unknown_coupon_raises():
    with pytest.raises(ValueError):
        calculate_total([{"qty": 1, "price": 10.0}], coupon="BOGUS")


@pytest.mark.parametrize("qty", [0, -1, 2.5, True, False, "2", None])
def test_calculate_total_rejects_bad_qty(qty):
    with pytest.raises(ValueError):
        calculate_total([{"qty": qty, "price": 10.0}])


@pytest.mark.parametrize(
    "price",
    [-0.01, -5, "nan", "inf", "-inf", float("nan"), float("inf"), True, None, "abc", 10**400],
)
def test_calculate_total_rejects_bad_price(price):
    with pytest.raises(ValueError):
        calculate_total([{"qty": 1, "price": price}])


def test_calculate_total_overflowing_cart_raises():
    with pytest.raises(ValueError):
        calculate_total([{"qty": 10**400, "price": 1.0}])


# ---------------------------------------------------------------------------
# POST /total (integration)
# ---------------------------------------------------------------------------

def test_total_happy_path(client):
    resp = client.post("/total", json={"items": [{"qty": 2, "price": 10.0}]})
    assert resp.status_code == 200
    assert resp.get_json() == {"total": 21.6}


def test_total_with_coupon(client):
    resp = client.post(
        "/total", json={"items": [{"qty": 5, "price": 10.0}], "coupon": "SAVE10"}
    )
    assert resp.status_code == 200
    assert resp.get_json() == {"total": 43.2}


def test_total_empty_cart(client):
    resp = client.post("/total", json={"items": []})
    assert resp.status_code == 200
    assert resp.get_json() == {"total": 0.0}


def test_total_unknown_coupon(client):
    resp = client.post("/total", json={"items": [{"qty": 1, "price": 1.0}], "coupon": "NOPE"})
    assert resp.status_code == 400
    assert resp.get_json() == {"error": "invalid cart"}


def test_total_missing_items_key(client):
    resp = client.post("/total", json={"coupon": "SAVE10"})
    assert resp.status_code == 400
    assert resp.get_json() == {"error": "invalid cart"}


def test_total_bad_qty(client):
    resp = client.post("/total", json={"items": [{"qty": 0, "price": 1.0}]})
    assert resp.status_code == 400
    assert resp.get_json() == {"error": "invalid cart"}


def test_total_negative_price(client):
    resp = client.post("/total", json={"items": [{"qty": 1, "price": -1.0}]})
    assert resp.status_code == 400
    assert resp.get_json() == {"error": "invalid cart"}


def test_total_nan_price(client):
    resp = client.post("/total", json={"items": [{"qty": 1, "price": float("nan")}]})
    assert resp.status_code == 400
    assert resp.get_json() == {"error": "invalid cart"}


def test_total_huge_int_price(client):
    resp = client.post("/total", json={"items": [{"qty": 1, "price": 10**400}]})
    assert resp.status_code == 400
    assert resp.get_json() == {"error": "invalid cart"}


def test_total_non_object_body(client):
    resp = client.post("/total", json=[1, 2, 3])
    assert resp.status_code == 400
    assert resp.get_json() == {"error": "invalid cart"}


def test_total_malformed_json(client):
    resp = client.post("/total", data="{not json", content_type="application/json")
    assert resp.status_code == 400
    assert resp.get_json() == {"error": "invalid cart"}


def test_total_empty_body_without_content_type(client):
    resp = client.post("/total")
    assert resp.status_code == 400
    assert resp.get_json() == {"error": "invalid cart"}


def test_total_plain_text_body(client):
    resp = client.post("/total", data="hello", content_type="text/plain")
    assert resp.status_code == 400
    assert resp.get_json() == {"error": "invalid cart"}
