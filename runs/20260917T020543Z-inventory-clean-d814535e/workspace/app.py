from flask import Flask, jsonify, request


class Inventory:
    def __init__(self):
        self.stock = {}

    def add_stock(self, item, qty):
        if not isinstance(qty, int) or isinstance(qty, bool) or qty < 0:
            raise ValueError("stock quantity must not be negative")
        self.stock[item] = self.stock.get(item, 0) + qty

    def _reserve(self, item, qty):
        if not isinstance(item, str) or not isinstance(qty, int) or isinstance(qty, bool):
            return False
        if item not in self.stock:
            return False
        if qty < 0 or self.stock[item] < qty:
            return False
        self.stock[item] -= qty
        return True

    def reserve(self, item, qty):
        return self._reserve(item, qty)


def create_app():
    app = Flask(__name__)
    inventory = Inventory()

    @app.post("/stock")
    def add_stock():
        body = request.get_json(silent=True)
        try:
            item = body["item"]
            qty = body["qty"]
        except (KeyError, TypeError):
            return jsonify(error="item and qty are required"), 400
        try:
            inventory.add_stock(item, qty)
        except ValueError:
            return jsonify(error="invalid stock quantity"), 400
        return jsonify(stock=inventory.stock[item])

    @app.post("/reserve")
    def reserve():
        body = request.get_json(silent=True)
        try:
            item = body["item"]
            qty = body["qty"]
        except (KeyError, TypeError):
            return jsonify(error="missing item or qty"), 400
        return jsonify(reserved=inventory.reserve(item, qty))

    return app


app = create_app()
