from flask import Flask, jsonify, request


TAX_RATE = 0.08


def calculate_total(items, coupon=None):
    subtotal = 0.0
    for item in items:
        qty = item["qty"]
        if not isinstance(qty, int) or isinstance(qty, bool) or qty <= 0:
            raise ValueError("qty must be a positive integer")
        price = float(item["price"])
        if price < 0:
            raise ValueError("price must not be negative")
        subtotal += price * qty

    if coupon is not None and coupon != "SAVE10":
        raise ValueError("unknown coupon")
    discount = 10.0 if coupon == "SAVE10" and subtotal >= 50 else 0.0
    discounted = subtotal - discount
    taxed = discounted * (1 + TAX_RATE)
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