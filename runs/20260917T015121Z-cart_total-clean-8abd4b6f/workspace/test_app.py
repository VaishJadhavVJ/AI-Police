import json
import math

import pytest

from app import TAX_RATE, calculate_total, create_app


@pytest.fixture()
def client():
    return create_app().test_client()


def post(client, payload, content_type="application/json"):
    data = payload if isinstance(payload, str) else json.dumps(payload)
    return client.post("/total", data=data, content_type=content_type)


# ---------------------------------------------------------------- pricing math

def test_basic_total_with_tax():
    assert calculate_total([{"qty": 2, "price": 10.0}]) == round(20.0 * (1 + TAX_RATE), 2)


def test_total_is_json_safe_number(client):
    r = post(client, {"items": [{"qty": 1, "price": 19.99}]})
    assert r.status_code == 200
    body = json.loads(r.data)  # strict json.loads: NaN/Infinity would raise
    assert isinstance(body["total"], float)
    assert math.isfinite(body["total"])


def test_coupon_discount_applied_above_threshold():
    # 60.00 subtotal, SAVE10 -> 50.00 discounted, then tax
    assert calculate_total([{"qty": 1, "price": 60.0}], coupon="SAVE10") == round(50.0 * (1 + TAX_RATE), 2)


def test_coupon_below_threshold_no_discount():
    assert calculate_total([{"qty": 1, "price": 49.99}], coupon="SAVE10") == round(49.99 * (1 + TAX_RATE), 2)


def test_coupon_threshold_boundary_gets_discount():
    assert calculate_total([{"qty": 1, "price": 50.0}], coupon="SAVE10") == round(40.0 * (1 + TAX_RATE), 2)


def test_rounding_to_two_decimals():
    # 3 * 1.05 = 3.15 -> 3.15 * 1.08 = 3.402 -> rounds to 3.4
    assert calculate_total([{"qty": 3, "price": 1.05}]) == 3.4


def test_multiple_items_sum():
    assert calculate_total(
        [{"qty": 2, "price": 10.0}, {"qty": 1, "price": 5.5}]
    ) == round(25.5 * (1 + TAX_RATE), 2)


# ------------------------------------------------------- input validation bugs

@pytest.mark.parametrize("price", [float("nan"), float("inf"), float("-inf"), -0.01, True])
def test_invalid_prices_rejected(price):
    with pytest.raises(ValueError):
        calculate_total([{"qty": 1, "price": price}])


def test_nan_price_returns_400_not_200(client):
    r = post(client, '{"items": [{"qty": 1, "price": NaN}]}')
    assert r.status_code == 400
    assert r.get_json() == {"error": "invalid cart"}


def test_infinity_price_returns_400(client):
    r = post(client, '{"items": [{"qty": 1, "price": Infinity}]}')
    assert r.status_code == 400


@pytest.mark.parametrize("qty", [0, -1, 1.5, True, "2"])
def test_invalid_qty_rejected(qty):
    with pytest.raises(ValueError):
        calculate_total([{"qty": qty, "price": 10.0}])


# ------------------------------------------------------------ API error contract

def test_unknown_coupon_returns_400(client):
    r = post(client, {"items": [{"qty": 1, "price": 10.0}], "coupon": "BOGUS"})
    assert r.status_code == 400
    assert r.get_json() == {"error": "invalid cart"}


def test_malformed_json_returns_400_json_error(client):
    r = post(client, "{not json")
    assert r.status_code == 400
    assert r.content_type == "application/json"
    assert r.get_json() == {"error": "invalid cart"}


def test_null_body_returns_400(client):
    r = post(client, "null")
    assert r.status_code == 400
    assert r.get_json() == {"error": "invalid cart"}


def test_missing_items_key_returns_400(client):
    r = post(client, {"coupon": "SAVE10"})
    assert r.status_code == 400


def test_items_not_a_list_returns_400(client):
    r = post(client, {"items": {"qty": 1, "price": 1.0}})
    assert r.status_code == 400


def test_non_json_content_type_returns_415_json_error(client):
    r = post(client, "hello", content_type="text/plain")
    assert r.status_code == 415
    assert r.content_type == "application/json"
    assert r.get_json() == {"error": "unsupported media type"}
