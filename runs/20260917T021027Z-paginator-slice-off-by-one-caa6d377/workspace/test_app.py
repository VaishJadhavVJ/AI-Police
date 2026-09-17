"""Tests for the pagination behavior in app.py."""

import pytest

from app import create_app, paginate


def test_first_page_starts_at_first_item():
    items = list(range(10))
    result = paginate(items, 1, 3)
    assert result["items"] == [0, 1, 2]


def test_second_page_follows_first():
    items = list(range(10))
    result = paginate(items, 2, 3)
    assert result["items"] == [3, 4, 5]


def test_no_item_is_lost_across_all_pages():
    items = list(range(10))
    seen = []
    for page in range(1, 5):  # ceil(10 / 3) = 4 pages
        result = paginate(items, page, 3)
        seen.extend(result["items"])
    assert seen == items


def test_page_holding_the_first_item():
    # First item should appear when its page is requested.
    items = ["a", "b", "c"]
    result = paginate(items, 1, 2)
    assert result["items"] == ["a", "b"]


def test_single_exact_page():
    result = paginate([1, 2, 3, 4], 1, 4)
    assert result["items"] == [1, 2, 3, 4]


def test_invalid_arguments_raise():
    with pytest.raises(ValueError):
        paginate([1, 2], 0, 2)
    with pytest.raises(ValueError):
        paginate([1, 2], 1, 0)
    with pytest.raises(ValueError):
        paginate([1, 2], 5, 2)  # page out of range


def test_paginate_route():
    client = create_app().test_client()
    resp = client.post(
        "/paginate", json={"items": [0, 1, 2, 3, 4], "page": 1, "page_size": 2}
    )
    assert resp.status_code == 200
    body = resp.get_json()
    assert body["items"] == [0, 1]
    assert body["page"] == 1
    assert body["page_size"] == 2
    assert body["total_pages"] == 3


def test_paginate_route_invalid():
    client = create_app().test_client()
    resp = client.post("/paginate", json={"items": [1, 2], "page": 9, "page_size": 2})
    assert resp.status_code == 400
