import math

from flask import Flask, jsonify, request


TAX_RATE = 0.08


def calculate_total(items, coupon=None):
    subtotal = 0.0
    for item in items:
        qty = item["qty"]
        if not isinstance(qty, int) or isinstance(qty, bool) or qty <= 0:
            raise ValueError("qty must be a positive integer")
        price = float(item["price"])
        if isinstance(item["price"], bool) or not math.isfinite(price) or price < 0:
            raise ValueError("price must be a finite, non-negative number")
        subtotal += price * qty

    if coupon is not None and coupon != "SAVE10":
        raise ValueError("unknown coupon")
    discount = 10.0 if coupon == "SAVE10" and subtotal >= 50 else 0.0
    taxed = (subtotal - discount) * (1 + TAX_RATE)
    total = round(taxed, 2)
    return total


def create_app():
    app = Flask(__name__)

    @app.post("/total")
    def total():
        if not request.is_json:
            return jsonify(error="unsupported media type"), 415
        try:
            # silent=True so malformed JSON comes back as None instead of
            # aborting with Flask's default HTML 400 page.
            body = request.get_json(silent=True)
            if not isinstance(body, dict):
                raise ValueError("body must be a JSON object")
            total = calculate_total(body["items"], body.get("coupon"))
        except (KeyError, TypeError, ValueError):
            return jsonify(error="invalid cart"), 400
        return jsonify(total=total)

    return app


app = create_app()
