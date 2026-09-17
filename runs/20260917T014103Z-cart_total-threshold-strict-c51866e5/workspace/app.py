from decimal import Decimal, InvalidOperation, ROUND_HALF_UP

from flask import Flask, jsonify, request


TAX_RATE = 0.08

COUPON_SAVE10 = "SAVE10"
COUPON_SAVE10_DISCOUNT_CENTS = 1000  # $10.00 off
# SAVE10 applies to orders of $50.00 or more (inclusive).
COUPON_SAVE10_MIN_SUBTOTAL_CENTS = 5000


def _to_cents(price):
    """Convert a dollar amount to integer cents without float drift.

    Accepts ints/floats/numeric strings; raises ValueError for anything that
    is not a finite, non-negative-capable number (the caller validates sign).
    """
    try:
        cents = (Decimal(str(price)) * 100).quantize(
            Decimal("1"), rounding=ROUND_HALF_UP
        )
    except (InvalidOperation, ValueError, TypeError):
        raise ValueError("price must be a valid number")
    return int(cents)


def calculate_total(items, coupon=None):
    subtotal_cents = 0
    for item in items:
        qty = item["qty"]
        if not isinstance(qty, int) or isinstance(qty, bool) or qty <= 0:
            raise ValueError("qty must be a positive integer")
        price = float(item["price"])
        if price < 0:
            raise ValueError("price must not be negative")
        subtotal_cents += _to_cents(price) * qty

    if coupon is not None and coupon != COUPON_SAVE10:
        raise ValueError("unknown coupon")
    discount_cents = (
        COUPON_SAVE10_DISCOUNT_CENTS
        if coupon == COUPON_SAVE10
        and subtotal_cents >= COUPON_SAVE10_MIN_SUBTOTAL_CENTS
        else 0
    )
    taxed = ((subtotal_cents - discount_cents) / 100.0) * (1 + TAX_RATE)
    total = round(taxed, 2)
    return total


def create_app():
    app = Flask(__name__)

    @app.post("/total")
    def total():
        try:
            body = request.get_json()
            total = calculate_total(body["items"], body.get("coupon"))
        except (KeyError, TypeError, ValueError):
            return jsonify(error="invalid cart"), 400
        return jsonify(total=total)

    return app


app = create_app()
