import threading

from flask import Flask, jsonify, request


class Inventory:
    def __init__(self):
        self.stock = {}
        # Guards stock mutations so add/reserve are atomic under threaded servers.
        self._lock = threading.Lock()

    def add_stock(self, item, qty):
        if not isinstance(qty, int) or isinstance(qty, bool) or qty < 0:
            raise ValueError("stock quantity must not be negative")
        with self._lock:
            self.stock[item] = self.stock.get(item, 0) + qty

    def _reserve(self, item, qty):
        if not isinstance(item, str) or not isinstance(qty, int) or isinstance(qty, bool):
            return False
        with self._lock:
            if qty < 0 or self.stock.get(item, 0) < qty:
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
            inventory.add_stock(body["item"], body["qty"])
        except (KeyError, TypeError, ValueError):
            return jsonify(error="invalid stock quantity"), 400
        return jsonify(stock=inventory.stock[body["item"]])

    @app.post("/reserve")
    def reserve():
        body = request.get_json(silent=True)
        if not isinstance(body, dict) or "item" not in body or "qty" not in body:
            return jsonify(error="item and qty are required"), 400
        reserved = inventory.reserve(body["item"], body["qty"])
        return jsonify(reserved=reserved)

    return app


app = create_app()
