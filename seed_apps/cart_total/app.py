from flask import Flask, jsonify, request


TAX_RATE = 0.10
COUPON_RATE = 0.10


def calculate_total(items):
    subtotal = 0.0
    for item in items:
        quantity = item["quantity"]
        if not isinstance(quantity, int) or isinstance(quantity, bool) or quantity <= 0:
            raise ValueError("quantity must be a positive integer")
        subtotal += float(item["price"]) * quantity

    discount = subtotal * COUPON_RATE if subtotal >= 100 else 0.0
    total = round((subtotal - discount) * (1 + TAX_RATE), 2)
    return total


def create_app():
    app = Flask(__name__)

    @app.post("/cart/total")
    def cart_total():
        try:
            total = calculate_total(request.get_json()["items"])
        except (KeyError, TypeError, ValueError):
            return jsonify(error="invalid cart"), 400
        return jsonify(total=total)

    return app


app = create_app()