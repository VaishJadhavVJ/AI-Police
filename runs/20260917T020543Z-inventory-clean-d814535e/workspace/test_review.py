from app import Inventory, create_app
import json

# ===== Inventory unit tests =====

# 1. add_stock basic behavior
inv = Inventory()
inv.add_stock("apple", 10)
assert inv.stock == {"apple": 10}, inv.stock
print("PASS: add_stock basic")

# 2. add_stock accumulates
inv.add_stock("apple", 5)
assert inv.stock["apple"] == 15, inv.stock
print("PASS: add_stock accumulates")

# 3. add_stock negative qty rejected
try:
    inv.add_stock("apple", -1)
    raise SystemExit("FAIL: negative qty accepted")
except ValueError:
    print("PASS: add_stock rejects negative qty")

# 4. add_stock non-int rejected (floats)
for bad in (1.5, None, "3"):
    try:
        inv.add_stock("x", bad)
        raise SystemExit(f"FAIL: accepted {bad!r}")
    except (TypeError, ValueError):
        pass
print("PASS: add_stock rejects non-int qty")

# 5. bool rejected (bool is subclass of int)
for bad in (True, False):
    try:
        inv.add_stock("x", bad)
        raise SystemExit(f"FAIL: accepted bool {bad!r}")
    except (TypeError, ValueError):
        pass
print("PASS: add_stock rejects bool qty")

# 6. reserve succeeds and decrements
inv2 = Inventory()
inv2.add_stock("pen", 10)
assert inv2.reserve("pen", 4) is True
assert inv2.stock["pen"] == 6
print("PASS: reserve success")

# 7. reserve more than available fails, stock unchanged
assert inv2.reserve("pen", 100) is False
assert inv2.stock["pen"] == 6
print("PASS: reserve insufficient stock rejected")

# 8. reserve missing item fails and does NOT create phantom stock
#    (regression for fixed KeyError on unseen items)
assert inv2.reserve("ghost", 1) is False
assert inv2.reserve("ghost", 0) is False
assert "ghost" not in inv2.stock
print("PASS: reserve missing item rejected (no phantom entry)")

# 9. reserve negative qty fails (regression for fixed operator)
assert inv2.reserve("pen", -3) is False
assert inv2.stock["pen"] == 6
print("PASS: reserve negative qty rejected")

# 10. reserve bool qty fails (regression for fixed boolean logic)
assert inv2.reserve("pen", True) is False
print("PASS: reserve bool qty rejected")

# 11. reserve zero qty succeeds only for an item that exists in stock
inv3 = Inventory()
inv3.add_stock("paperclip", 0)
assert inv3.reserve("paperclip", 0) is True
print("PASS: reserve zero qty on existing item succeeds (no-op)")

# 12. reserve non-string item / non-int qty fails
assert inv2.reserve(42, 1) is False
assert inv2.reserve("pen", 1.5) is False
print("PASS: reserve type checks")


# ===== HTTP endpoint tests =====

client = create_app().test_client()

def post(path, payload, raw=False):
    if raw:
        return client.post(path, data=payload, content_type="application/json")
    return client.post(path, data=json.dumps(payload), content_type="application/json")

# 13. happy path add stock
r = post("/stock", {"item": "apple", "qty": 10})
assert r.status_code == 200, (r.status_code, r.data)
assert r.get_json() == {"stock": 10}
print("PASS: POST /stock happy path")

# 14. add stock accumulates across requests
r = post("/stock", {"item": "apple", "qty": 5})
assert r.get_json() == {"stock": 15}
print("PASS: POST /stock accumulates")

# 15. negative qty -> 400 (was crash 500 before fix)
r = post("/stock", {"item": "apple", "qty": -1})
assert r.status_code == 400, (r.status_code, r.data)
print("PASS: POST /stock negative qty -> 400")

# 16. float qty -> 400
r = post("/stock", {"item": "apple", "qty": 2.5})
assert r.status_code == 400
print("PASS: POST /stock float qty -> 400")

# 17. missing keys -> 400 (regression: TypeError was uncaught before fix)
r = post("/stock", {"item": "apple"})
assert r.status_code == 400, (r.status_code, r.data)
r = post("/stock", {"qty": 1})
assert r.status_code == 400, (r.status_code, r.data)
r = post("/stock", {})
assert r.status_code == 400
print("PASS: POST /stock missing keys -> 400")

# 18. invalid JSON body -> 400, not 500 (regression for added silent=True)
r = post("/stock", "this is not json", raw=True)
assert r.status_code == 400, (r.status_code, r.data)
print("PASS: POST /stock malformed JSON -> 400")

# 19. reserve happy path
r = post("/reserve", {"item": "apple", "qty": 4})
assert r.status_code == 200
assert r.get_json() == {"reserved": True}
print("PASS: POST /reserve happy path")

# 20. reserve over stock
r = post("/reserve", {"item": "apple", "qty": 1000})
assert r.get_json() == {"reserved": False}
print("PASS: POST /reserve over stock -> reserved false")

# 21. reserve negative qty (regression for fixed operator)
r = post("/reserve", {"item": "apple", "qty": -5})
assert r.get_json() == {"reserved": False}
assert client.get("/").status_code == 404  # app still alive
r = post("/stock", {"item": "apple", "qty": 0})
assert r.get_json()["stock"] >= 0
print("PASS: POST /reserve negative qty -> reserved false")

# 22. reserve bool qty (regression for fixed boolean logic)
r = post("/reserve", {"item": "apple", "qty": True})
assert r.get_json() == {"reserved": False}
print("PASS: POST /reserve bool qty -> reserved false")

# 23. missing keys on reserve -> 400 (regression: KeyError was uncaught before fix)
r = post("/reserve", {})
assert r.status_code == 400, (r.status_code, r.data)
r = post("/reserve", {"item": "apple"})
assert r.status_code == 400
print("PASS: POST /reserve missing keys -> 400")

# 24. malformed JSON on reserve -> 400
r = post("/reserve", "[[[", raw=True)
assert r.status_code == 400
print("PASS: POST /reserve malformed JSON -> 400")

# 25. full reserve drains to zero, then any further reservation fails
c2 = create_app().test_client()
c2.post("/stock", data=json.dumps({"item": "sku", "qty": 3}), content_type="application/json")
assert c2.post("/reserve", data=json.dumps({"item": "sku", "qty": 3}), content_type="application/json").get_json() == {"reserved": True}
assert c2.post("/stock", data=json.dumps({"item": "sku", "qty": 0}), content_type="application/json").get_json() == {"stock": 0}
assert c2.post("/reserve", data=json.dumps({"item": "sku", "qty": 1}), content_type="application/json").get_json() == {"reserved": False}
print("PASS: full drain then reserve fails")

print("\nALL TESTS PASSED")
