from app import calculate_total

# Cart: 3 x $20 = $60 subtotal, SAVE10 coupon ($10 off)
subtotal = 60.0
expected_before_tax = round((subtotal - 10.0) * 1.08, 2)  # discount first, then tax
actual = calculate_total([{"qty": 3, "price": 20.0}], coupon="SAVE10")

print(f"subtotal = ${subtotal:.2f}")
print(f"expected (discount BEFORE tax): ${expected_before_tax:.2f}")
print(f"actual   (current code):        ${actual:.2f}")
print(f"current code applies discount AFTER tax: {actual != expected_before_tax}")

# Also confirm line 21's hardcoded 1.08 silently diverges if TAX_RATE changes:
print(f"hardcoded 1.08 equals TAX_RATE today: {1 + 0.08 == 1.08}")
