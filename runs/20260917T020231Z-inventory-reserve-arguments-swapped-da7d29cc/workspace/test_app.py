"""Regression tests for the reservation bug in app.py.

The original bug: Inventory.reserve() called self._reserve(qty, item),
transposing the arguments. _reserve's first parameter is `item`, so the
isinstance(item, str) guard always failed and every reservation returned
False, even with ample stock.
"""

import pytest

from app import Inventory, create_app


@pytest.fixture()
def inventory():
    inv = Inventory()
    inv.add_stock("widget", 10)
    return inv


def test_reserve_succeeds_and_decrements_stock(inventory):
    assert inventory.reserve("widget", 3) is True
    assert inventory.stock["widget"] == 7


def test_reserve_exact_remaining_amount(inventory):
    assert inventory.reserve("widget", 10) is True
    assert inventory.stock["widget"] == 0


def test_reserve_more_than_available_fails(inventory):
    assert inventory.reserve("widget", 11) is False
    assert inventory.stock["widget"] == 10


def test_reserve_unknown_item_fails(inventory):
    assert inventory.reserve("nonexistent", 1) is False


@pytest.mark.parametrize(
    "item, qty",
    [
        ("widget", -1),      # negative quantity
        ("widget", True),    # bool is not an acceptable quantity
        (123, 1),            # non-string item
        ("widget", 1.5),     # non-int quantity
        (None, None),
    ],
)
def test_reserve_invalid_input_fails(inventory, item, qty):
    assert inventory.reserve(item, qty) is False
    assert inventory.stock["widget"] == 10


def test_reserve_via_http():
    client = create_app().test_client()
    assert client.post("/stock", json={"item": "gizmo", "qty": 100}).get_json() == {"stock": 100}
    assert client.post("/reserve", json={"item": "gizmo", "qty": 25}).get_json() == {"reserved": True}
    assert client.post("/stock", json={"item": "gizmo", "qty": 0}).get_json() == {"stock": 75}
