import pytest

from app import calculate_total


def test_no_coupon():
    # 60 * 1.08 = 64.80
    assert calculate_total([{"qty": 2, "price": 30.0}]) == 64.80


def test_save10_discount_applied_before_tax():
    # (60 - 10) * 1.08 = 54.00  (bug taxed the full subtotal first: 54.80)
    assert calculate_total([{"qty": 2, "price": 30.0}], "SAVE10") == 54.00


def test_save10_is_flat_10_off_pretax():
    # Coupon is a flat $10 off the subtotal; tax applies to the
    # discounted amount, so the customer saves 10 * 1.08 = 10.80.
    items = [{"qty": 3, "price": 19.99}]  # subtotal 59.97
    without = calculate_total(items)  # 59.97 * 1.08 = 64.77
    with_coupon = calculate_total(items, "SAVE10")  # 49.97 * 1.08 = 53.97
    assert with_coupon == 53.97
    assert round(without - with_coupon, 2) == 10.80


def test_save10_below_minimum_gets_no_discount():
    assert calculate_total([{"qty": 1, "price": 40.0}], "SAVE10") == 43.20


def test_save10_discount_exactly_at_threshold():
    # (50 - 10) * 1.08 = 43.20
    assert calculate_total([{"qty": 1, "price": 50.0}], "SAVE10") == 43.20


def test_unknown_coupon_raises():
    with pytest.raises(ValueError):
        calculate_total([{"qty": 1, "price": 10.0}], "BOGUS")


def test_invalid_qty_raises():
    with pytest.raises(ValueError):
        calculate_total([{"qty": 0, "price": 10.0}])


def test_negative_price_raises():
    with pytest.raises(ValueError):
        calculate_total([{"qty": 1, "price": -1.0}])


def test_rounding_to_cents():
    # (3 * 19.99 - 10) * 1.08 = 49.97 * 1.08 = 53.9676 -> 53.97
    assert calculate_total([{"qty": 3, "price": 19.99}], "SAVE10") == 53.97
