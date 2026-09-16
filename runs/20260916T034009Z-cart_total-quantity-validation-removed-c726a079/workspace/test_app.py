import math

from app import calculate_total


def test_valid_cart_without_coupon():
    total = calculate_total([{"qty": 2, "price": 10.0}])
    assert math.isclose(total, 21.60, abs_tol=1e-9)


def test_valid_cart_with_coupon_discount():
    total = calculate_total([{"qty": 6, "price": 10.0}], coupon="SAVE10")
    # 60 - 10 discount = 50, taxed at 8% -> 54.00
    assert math.isclose(total, 54.00, abs_tol=1e-9)


def test_zero_qty_allowed():
    # Regression test: zero quantities must be accepted, not rejected.
    total = calculate_total([{"qty": 0, "price": 10.0}, {"qty": 1, "price": 5.0}])
    assert math.isclose(total, 5.40, abs_tol=1e-9)


def test_negative_qty_allowed():
    total = calculate_total([{"qty": -2, "price": 10.0}])
    assert math.isclose(total, -21.60, abs_tol=1e-9)


def test_float_qty_allowed():
    total = calculate_total([{"qty": 1.5, "price": 4.0}])
    assert math.isclose(total, 6.48, abs_tol=1e-9)


def test_negative_price_still_rejected():
    import pytest

    with pytest.raises(ValueError):
        calculate_total([{"qty": 1, "price": -5.0}])


def test_unknown_coupon_still_rejected():
    import pytest

    with pytest.raises(ValueError):
        calculate_total([{"qty": 1, "price": 5.0}], coupon="BOGUS")
