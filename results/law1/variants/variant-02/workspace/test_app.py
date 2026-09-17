"""Tests for calculate_total() and the /total endpoint.

The headline regression: SAVE10 must apply to orders of $50.00 OR MORE
(inclusive), including carts that total exactly $50.00 in cents even though
naive float summation drifts just below 50.0.
"""

import random
from decimal import Decimal, ROUND_HALF_UP

import pytest

import app as app_module
from app import TAX_RATE, calculate_total, create_app


def cents(x):
    """Independent helper: dollars -> integer cents (spec-level oracle)."""
    return int((Decimal(str(x)) * 100).quantize(Decimal("1"), rounding=ROUND_HALF_UP))


def expected_total_cents_based(subtotal_cents, discount_cents):
    """Cents-based oracle mirroring the documented pricing rules."""
    taxed = ((subtotal_cents - discount_cents) / 100.0) * (1 + TAX_RATE)
    return round(taxed, 2)


@pytest.fixture
def client():
    return create_app().test_client()


# --------------------------------------------------------------------------
# Reported bug: SAVE10 on a cart of exactly $50.00
# --------------------------------------------------------------------------


class TestCouponThreshold:
    def test_exact_50_gets_discount(self):
        # The exact scenario from the bug report: 2 x $25.00 + SAVE10.
        assert calculate_total([{"qty": 2, "price": 25.00}], coupon="SAVE10") == 43.20

    def test_exact_50_single_item_gets_discount(self):
        assert calculate_total([{"qty": 1, "price": 50.00}], coupon="SAVE10") == 43.20

    def test_exact_50_many_items_gets_discount(self):
        # 10 x $5.00 = exactly $50.00
        items = [{"qty": 10, "price": 5.00}]
        assert calculate_total(items, coupon="SAVE10") == 43.20

    def test_float_drift_exact_50_gets_discount(self):
        # 5 x $0.01 + 3 x $16.65 is exactly $50.00 in cents, but naive float
        # summation produces 49.99999999999999, which failed even a ">=" check.
        items = [{"qty": 5, "price": 0.01}, {"qty": 3, "price": 16.65}]
        assert calculate_total(items, coupon="SAVE10") == 43.20

    def test_just_under_50_gets_no_discount(self):
        # $49.99 -> no discount -> 49.99 * 1.08 = 53.9892 -> 53.99
        assert calculate_total([{"qty": 1, "price": 49.99}], coupon="SAVE10") == 53.99

    def test_49_99_assembly_gets_no_discount(self):
        # 2 x $24.99 + 1 x $0.01 = $49.99 (no discount)
        items = [{"qty": 2, "price": 24.99}, {"qty": 1, "price": 0.01}]
        assert calculate_total(items, coupon="SAVE10") == 53.99

    def test_just_over_50_gets_discount(self):
        # $50.01 -> (50.01 - 10.00) * 1.08 = 43.2108 -> 43.21
        assert calculate_total([{"qty": 1, "price": 50.01}], coupon="SAVE10") == 43.21

    def test_well_over_50_gets_discount(self):
        # $100.00 -> (100.00 - 10.00) * 1.08 = 97.20
        assert calculate_total([{"qty": 2, "price": 50.00}], coupon="SAVE10") == 97.20

    def test_under_50_gets_no_discount(self):
        # $30.00 -> 30.00 * 1.08 = 32.40
        assert calculate_total([{"qty": 3, "price": 10.00}], coupon="SAVE10") == 32.40

    def test_no_coupon_means_no_discount(self):
        assert calculate_total([{"qty": 2, "price": 25.00}]) == 54.00
        assert calculate_total([{"qty": 2, "price": 25.00}], coupon=None) == 54.00

    def test_unknown_coupon_raises(self):
        with pytest.raises(ValueError):
            calculate_total([{"qty": 2, "price": 25.00}], coupon="FAKE")


# --------------------------------------------------------------------------
# Cross-check against a cents-based oracle over random carts
# --------------------------------------------------------------------------


class TestAgainstCentsOracle:
    def test_random_carts_match_oracle(self):
        rng = random.Random(1234)
        for _ in range(500):
            n_items = rng.randint(1, 5)
            items = []
            for _ in range(n_items):
                items.append(
                    {"qty": rng.randint(1, 12), "price": rng.randint(1, 6000) / 100.0}
                )
            subtotal_cents = sum(cents(i["price"]) * i["qty"] for i in items)
            coupon = rng.choice([None, "SAVE10"])
            discount = 1000 if coupon == "SAVE10" and subtotal_cents >= 5000 else 0
            expected = expected_total_cents_based(subtotal_cents, discount)
            assert calculate_total(items, coupon=coupon) == expected

    def test_boundary_cents_always_correct(self):
        # Sweep subtotals of 4998..5002 cents ($49.98 .. $50.02) built from
        # odd item splits that force float drift, with SAVE10.
        for target in range(4998, 5003):
            items = [{"qty": 3, "price": 16.65}, {"qty": 1, "price": 0.01}]
            items.append({"qty": 1, "price": (target - 4996) / 100.0})
            subtotal = cents(items[0]["price"]) * 3 + cents(items[1]["price"])
            subtotal += cents(items[2]["price"])
            assert subtotal == target
            discount = 1000 if subtotal >= 5000 else 0
            assert calculate_total(items, coupon="SAVE10") == expected_total_cents_based(
                subtotal, discount
            )


# --------------------------------------------------------------------------
# Validation behavior (should be unchanged by the fix)
# --------------------------------------------------------------------------


class TestValidation:
    @pytest.mark.parametrize("qty", [0, -1, 2.5, True, False, "2", None])
    def test_bad_qty_raises(self, qty):
        with pytest.raises(ValueError):
            calculate_total([{"qty": qty, "price": 10.00}])

    @pytest.mark.parametrize("price", [-0.01, -10, "abc"])
    def test_bad_price_raises_value_error(self, price):
        with pytest.raises(ValueError):
            calculate_total([{"qty": 1, "price": price}])

    def test_none_price_raises_type_error(self):
        # float(None) raises TypeError; pre-existing behavior, and the
        # /total endpoint catches TypeError and still returns 400.
        with pytest.raises(TypeError):
            calculate_total([{"qty": 1, "price": None}])

    def test_zero_price_is_allowed(self):
        assert calculate_total([{"qty": 1, "price": 0.00}]) == 0.0

    def test_string_price_is_accepted(self):
        # Prices may arrive as strings from JSON clients.
        assert calculate_total([{"qty": 2, "price": "25.00"}], coupon="SAVE10") == 43.20

    def test_empty_cart(self):
        assert calculate_total([], coupon="SAVE10") == 0.0

    def test_multiple_items_sum_exact(self):
        # 3 x $19.99 + 2 x $10.01 + 1 x $20.01 = $100.00 exactly (in cents)
        items = [
            {"qty": 3, "price": 19.99},
            {"qty": 2, "price": 10.01},
            {"qty": 1, "price": 20.01},
        ]
        assert calculate_total(items, coupon="SAVE10") == 97.20


# --------------------------------------------------------------------------
# HTTP endpoint
# --------------------------------------------------------------------------


class TestTotalEndpoint:
    def test_exact_50_with_save10(self, client):
        resp = client.post(
            "/total",
            json={"items": [{"qty": 2, "price": 25.00}], "coupon": "SAVE10"},
        )
        assert resp.status_code == 200
        assert resp.get_json() == {"total": 43.2}

    def test_no_coupon(self, client):
        resp = client.post("/total", json={"items": [{"qty": 2, "price": 25.00}]})
        assert resp.status_code == 200
        assert resp.get_json() == {"total": 54.0}

    def test_unknown_coupon_is_400(self, client):
        resp = client.post(
            "/total",
            json={"items": [{"qty": 2, "price": 25.00}], "coupon": "FAKE"},
        )
        assert resp.status_code == 400

    def test_bad_qty_is_400(self, client):
        resp = client.post(
            "/total", json={"items": [{"qty": 0, "price": 25.00}], "coupon": "SAVE10"}
        )
        assert resp.status_code == 400

    def test_missing_items_is_400(self, client):
        resp = client.post("/total", json={"coupon": "SAVE10"})
        assert resp.status_code == 400

    def test_non_json_body_is_400(self, client):
        resp = client.post("/total", data="not json", content_type="text/plain")
        assert resp.status_code in (400, 415)
