import math

from flask import Flask, jsonify, request


TAX_RATE = 0.08
COUPON_DISCOUNT = 10.0
COUPON_MIN_SUBTOTAL = 50.0
VALID_COUPONS = {"SAVE10"}


class InvalidCartError(ValueError):
    """Raised when a cart payload fails validation; maps to a 400 response."""


def _as_finite_float(value, what):
    """Coerce *value* to a finite float, raising InvalidCartError otherwise."""
    if isinstance(value, bool):
        raise InvalidCartError(f"{what} must be a finite number")
    try:
        number = float(value)
    except (TypeError, ValueError, OverflowError):
        raise InvalidCartError(f"{what} must be a finite number") from None
    if not math.isfinite(number):
        raise InvalidCartError(f"{what} must be a finite number")
    return number


def calculate_total(items, coupon=None):
    if not isinstance(items, (list, tuple)):
        raise InvalidCartError("items must be a list")

    subtotal = 0.0
    for item in items:
        if not isinstance(item, dict):
            raise InvalidCartError("each item must be an object")

        qty = item.get("qty")
        if isinstance(qty, bool) or not isinstance(qty, int) or qty <= 0:
            raise InvalidCartError("qty must be a positive integer")

        price = _as_finite_float(item.get("price"), "price")
        if price < 0:
            raise InvalidCartError("price must not be negative")

        try:
            subtotal += price * qty
        except OverflowError:
            raise InvalidCartError("cart total is too large") from None

    if not math.isfinite(subtotal):
        raise InvalidCartError("cart total is too large")

    if coupon is not None:
        if not isinstance(coupon, str) or coupon not in VALID_COUPONS:
            raise InvalidCartError("unknown coupon")
    discount = COUPON_DISCOUNT if coupon == "SAVE10" and subtotal >= COUPON_MIN_SUBTOTAL else 0.0

    taxed = (subtotal - discount) * (1 + TAX_RATE)
    return round(taxed, 2)


def create_app():
    app = Flask(__name__)

    @app.post("/total")
    def total():
        # silent=True: malformed JSON or a wrong Content-Type yields None
        # instead of raising, so every bad request below gets the same
        # JSON "invalid cart" error response.
        body = request.get_json(silent=True)
        if not isinstance(body, dict):
            return jsonify(error="invalid cart"), 400
        try:
            result = calculate_total(body.get("items"), body.get("coupon"))
        except InvalidCartError:
            return jsonify(error="invalid cart"), 400
        return jsonify(total=result)

    return app


app = create_app()
