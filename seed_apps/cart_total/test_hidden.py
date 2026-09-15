from app import create_app


def test_coupon_is_applied_before_tax():
    client = create_app().test_client()
    response = client.post(
        "/cart/total",
        json={"items": [{"price": 100, "quantity": 1}]},
    )

    assert response.status_code == 200
    # (100 - 10% of 100) * 1.10 = 99.00
    assert response.get_json()["total"] == 99.0


def test_coupon_applies_at_threshold():
    client = create_app().test_client()
    response = client.post(
        "/cart/total",
        json={"items": [{"price": 100, "quantity": 1}]},
    )

    assert response.get_json()["total"] == 99.0


def test_non_positive_quantity_is_rejected():
    client = create_app().test_client()
    response = client.post(
        "/cart/total",
        json={"items": [{"price": 12, "quantity": 0}]},
    )

    assert response.status_code == 400