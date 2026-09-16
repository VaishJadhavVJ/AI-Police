import math

from flask import Flask, jsonify, request


TAX_RATE = 0.08
COUPONS = {"SAVE10": 10.0}
COUPON_MIN_SUBTOTAL = 50.0


def calculate_total(items, coupon=None):
    subtotal = 0.0
    for item in items:
        try:
            qty = item["qty"]
            price = item["price"]
        except TypeError:
            raise ValueError("each item must be an object with qty and price") from None
        if not isinstance(qty, int) or isinstance(qty, bool) or qty <= 0:
            raise ValueError("qty must be a positive integer")
        if isinstance(price, bool) or not isinstance(price, (int, float, str)):
            raise ValueError("price must be a number")
        try:
            price = float(price)
        except (TypeError, ValueError, OverflowError):
            raise ValueError("price must be a finite number") from None
        if not math.isfinite(price) or price < 0:
            raise ValueError("price must be a finite, non-negative number")
        try:
            line = price * qty
        except OverflowError:
            raise ValueError("cart total is too large") from None
        if not math.isfinite(line):
            raise ValueError("cart total is too large")
        subtotal += line

    if coupon is not None:
        try:
            discount = COUPONS[coupon]
        except (KeyError, TypeError):
            raise ValueError("unknown coupon") from None
        if subtotal >= COUPON_MIN_SUBTOTAL:
            subtotal -= discount

    taxed = subtotal * (1 + TAX_RATE)
    if not math.isfinite(taxed):
        raise ValueError("cart total is too large")
    total = round(taxed, 2)
    return total


def create_app():
    app = Flask(__name__)

    @app.post("/total")
    def total():
        # silent=True: malformed JSON or a wrong Content-Type yields None
        # instead of raising an HTTPException we cannot turn into our
        # JSON error response here.
        body = request.get_json(silent=True)
        if not isinstance(body, dict):
            return jsonify(error="invalid cart"), 400
        try:
            total = calculate_total(body["items"], body.get("coupon"))
        except (KeyError, TypeError, ValueError):
            return jsonify(error="invalid cart"), 400
        return jsonify(total=total)

    return app


app = create_app()
