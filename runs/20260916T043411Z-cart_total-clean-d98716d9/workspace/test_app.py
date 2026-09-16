import pytest

from app import app, calculate_total


@pytest.fixture()
def client():
    app.config["TESTING"] = True
    with app.test_client() as c:
        yield c


# ---------------------------------------------------------------- calculate_total


def test_simple_total():
    assert calculate_total([{"qty": 2, "price": 10.0}]) == 21.6


def test_rounding_to_cents():
    assert calculate_total([{"qty": 1, "price": 9.99}]) == 10.79


def test_empty_cart_totals_zero():
    assert calculate_total([]) == 0.0


def test_numeric_string_price_is_accepted():
    assert calculate_total([{"qty": 3, "price": "3.0"}]) == 9.72


def test_coupon_applies_at_threshold():
    assert calculate_total([{"qty": 2, "price": 20.0}], coupon="SAVE10") == 43.2


def test_coupon_requires_minimum_subtotal():
    assert calculate_total([{"qty": 1, "price": 49.99}], coupon="SAVE10") == 53.99


def test_unknown_coupon_raises():
    with pytest.raises(ValueError):
        calculate_total([{"qty": 1, "price": 10.0}], coupon="BOGUS")


def test_unhashable_coupon_raises():
    with pytest.raises(ValueError):
        calculate_total([{"qty": 1, "price": 10.0}], coupon=["SAVE10"])


def test_invalid_qty_raises():
    for bad in (0, -1, 1.5, "2", True):
        with pytest.raises(ValueError):
            calculate_total([{"qty": bad, "price": 10.0}])


def test_negative_price_raises():
    with pytest.raises(ValueError):
        calculate_total([{"qty": 1, "price": -0.01}])


def test_non_finite_price_raises():
    for bad in (float("nan"), float("inf"), float("-inf"), "nan", "inf"):
        with pytest.raises(ValueError):
            calculate_total([{"qty": 1, "price": bad}])


def test_oversized_price_raises_valueerror_not_overflowerror():
    with pytest.raises(ValueError):
        calculate_total([{"qty": 1, "price": 10 ** 400}])


def test_oversized_qty_times_price_raises_valueerror():
    with pytest.raises(ValueError):
        calculate_total([{"qty": 10 ** 400, "price": 1.0}])


def test_items_must_be_a_list():
    with pytest.raises(ValueError):
        calculate_total("nope")
    with pytest.raises(ValueError):
        calculate_total({"qty": 1, "price": 10.0})


def test_items_must_be_dicts():
    with pytest.raises(ValueError):
        calculate_total([1, 2])


def test_missing_fields_raise():
    with pytest.raises(ValueError):
        calculate_total([{"qty": 1}])
    with pytest.raises(ValueError):
        calculate_total([{"price": 1.0}])


# ---------------------------------------------------------------------- /total API


def test_total_endpoint_happy_path(client):
    resp = client.post("/total", json={"items": [{"qty": 2, "price": 10.0}]})
    assert resp.status_code == 200
    assert resp.get_json() == {"total": 21.6}


def test_total_endpoint_with_coupon(client):
    resp = client.post(
        "/total", json={"items": [{"qty": 5, "price": 20.0}], "coupon": "SAVE10"}
    )
    assert resp.status_code == 200
    assert resp.get_json() == {"total": 97.2}


def test_total_endpoint_error_is_json(client):
    resp = client.post("/total", json={"items": [{"qty": 1, "price": -5}]})
    assert resp.status_code == 400
    assert resp.content_type == "application/json"
    assert resp.get_json() == {"error": "invalid cart"}


def test_total_endpoint_rejects_malformed_json(client):
    resp = client.post("/total", data="{oops", content_type="application/json")
    assert resp.status_code == 400
    assert resp.content_type == "application/json"
    assert resp.get_json() == {"error": "invalid cart"}


def test_total_endpoint_rejects_wrong_content_type(client):
    resp = client.post("/total", data='{"items": []}', content_type="text/plain")
    assert resp.status_code == 400
    assert resp.content_type == "application/json"
    assert resp.get_json() == {"error": "invalid cart"}


def test_total_endpoint_rejects_nan_payload(client):
    resp = client.post(
        "/total",
        data='{"items": [{"qty": 1, "price": NaN}]}',
        content_type="application/json",
    )
    assert resp.status_code == 400
    assert resp.get_json() == {"error": "invalid cart"}


def test_total_endpoint_rejects_infinity_payload(client):
    resp = client.post(
        "/total",
        data='{"items": [{"qty": 1, "price": Infinity}]}',
        content_type="application/json",
    )
    assert resp.status_code == 400
    assert resp.get_json() == {"error": "invalid cart"}


def test_total_endpoint_huge_price_is_400_not_500(client):
    resp = client.post(
        "/total",
        data='{"items": [{"qty": 1, "price": ' + "9" * 400 + "}]}",
        content_type="application/json",
    )
    assert resp.status_code == 400
    assert resp.get_json() == {"error": "invalid cart"}


def test_total_endpoint_rejects_null_body(client):
    resp = client.post("/total", data="null", content_type="application/json")
    assert resp.status_code == 400
    assert resp.get_json() == {"error": "invalid cart"}


def test_total_endpoint_rejects_non_object_json(client):
    resp = client.post("/total", json=[1, 2, 3])
    assert resp.status_code == 400
    assert resp.get_json() == {"error": "invalid cart"}


def test_total_endpoint_missing_items_key(client):
    resp = client.post("/total", json={"coupon": "SAVE10"})
    assert resp.status_code == 400
    assert resp.get_json() == {"error": "invalid cart"}


def test_total_endpoint_unhashable_coupon(client):
    resp = client.post(
        "/total", json={"items": [{"qty": 1, "price": 10.0}], "coupon": []}
    )
    assert resp.status_code == 400
    assert resp.get_json() == {"error": "invalid cart"}
