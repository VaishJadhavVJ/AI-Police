import unittest
from app import Inventory, create_app


class TestReserve(unittest.TestCase):
    def test_reserve_succeeds_with_plenty_in_stock(self):
        inv = Inventory()
        inv.add_stock("widget", 10)
        self.assertTrue(inv.reserve("widget", 3))
        self.assertEqual(inv.stock["widget"], 7)

    def test_reserve_exact_stock(self):
        inv = Inventory()
        inv.add_stock("widget", 5)
        self.assertTrue(inv.reserve("widget", 5))
        self.assertEqual(inv.stock["widget"], 0)

    def test_reserve_insufficient_stock_fails(self):
        inv = Inventory()
        inv.add_stock("widget", 2)
        self.assertFalse(inv.reserve("widget", 3))
        self.assertEqual(inv.stock["widget"], 2)  # unchanged

    def test_reserve_unknown_item_fails(self):
        inv = Inventory()
        self.assertFalse(inv.reserve("ghost", 1))

    def test_reserve_invalid_args_fail(self):
        inv = Inventory()
        inv.add_stock("widget", 10)
        self.assertFalse(inv.reserve("widget", -1))
        self.assertFalse(inv.reserve("widget", 1.5))
        self.assertFalse(inv.reserve(123, 1))


class TestReserveHTTP(unittest.TestCase):
    def setUp(self):
        self.client = create_app().test_client()

    def test_http_reserve_success(self):
        self.client.post("/stock", json={"item": "widget", "qty": 10})
        resp = self.client.post("/reserve", json={"item": "widget", "qty": 4})
        self.assertEqual(resp.status_code, 200)
        self.assertEqual(resp.get_json(), {"reserved": True})
        # stock actually decremented
        stock_resp = self.client.post("/stock", json={"item": "widget", "qty": 0})
        self.assertEqual(stock_resp.get_json()["stock"], 6)

    def test_http_reserve_insufficient(self):
        self.client.post("/stock", json={"item": "bolt", "qty": 1})
        resp = self.client.post("/reserve", json={"item": "bolt", "qty": 5})
        self.assertEqual(resp.get_json(), {"reserved": False})


if __name__ == "__main__":
    unittest.main()
