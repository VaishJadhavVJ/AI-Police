"""Tests for app.py pagination endpoint and helper."""

import json

import pytest

from app import create_app, paginate


@pytest.fixture()
def client():
    return create_app().test_client()


# --------------------------------------------------------------------------
# Unit tests for paginate()
# --------------------------------------------------------------------------


def test_paginate_first_page():
    result = paginate(list(range(10)), 1, 3)
    assert result == {"items": [0, 1, 2], "page": 1, "page_size": 3, "total_pages": 4}


def test_paginate_middle_page():
    result = paginate(list(range(10)), 3, 3)
    assert result["items"] == [6, 7, 8]
    assert result["total_pages"] == 4


def test_paginate_last_partial_page():
    result = paginate(list(range(10)), 4, 3)
    assert result["items"] == [9]
    assert result["total_pages"] == 4


def test_paginate_exact_multiple():
    result = paginate(list(range(9)), 3, 3)
    assert result["items"] == [6, 7, 8]
    assert result["total_pages"] == 3


def test_paginate_page_size_larger_than_items():
    result = paginate([1, 2, 3], 1, 100)
    assert result == {"items": [1, 2, 3], "page": 1, "page_size": 100, "total_pages": 1}


def test_paginate_single_item():
    result = paginate([42], 1, 1)
    assert result == {"items": [42], "page": 1, "page_size": 1, "total_pages": 1}


def test_paginate_empty_items_first_page_is_valid():
    """An empty collection has one (empty) page, so page 1 must succeed."""
    result = paginate([], 1, 10)
    assert result == {"items": [], "page": 1, "page_size": 10, "total_pages": 1}


def test_paginate_empty_items_page_two_is_out_of_range():
    with pytest.raises(ValueError):
        paginate([], 2, 10)


def test_paginate_rejects_page_out_of_range():
    with pytest.raises(ValueError):
        paginate(list(range(10)), 5, 3)  # total_pages == 4


def test_paginate_rejects_non_positive_page_and_size():
    for bad in (0, -1):
        with pytest.raises(ValueError):
            paginate([1], bad, 1)
        with pytest.raises(ValueError):
            paginate([1], 1, bad)


def test_paginate_rejects_booleans():
    # bool is a subclass of int; True/False must not be accepted as numbers here.
    with pytest.raises(TypeError):
        paginate([1], True, 10)
    with pytest.raises(TypeError):
        paginate([1], 1, False)


def test_paginate_rejects_non_integer_numbers():
    with pytest.raises(TypeError):
        paginate(list(range(10)), 1.5, 3)
    with pytest.raises(TypeError):
        paginate(list(range(10)), 1, 2.5)


def test_paginate_rejects_non_sequence_items():
    with pytest.raises(TypeError):
        paginate("hello", 1, 2)  # a string is not a list of items
    with pytest.raises(TypeError):
        paginate(None, 1, 2)
    with pytest.raises(TypeError):
        paginate(5, 1, 2)


def test_paginate_accepts_tuples():
    assert paginate((1, 2, 3, 4), 2, 2) == {
        "items": [3, 4],
        "page": 2,
        "page_size": 2,
        "total_pages": 2,
    }


# --------------------------------------------------------------------------
# Endpoint tests for POST /paginate
# --------------------------------------------------------------------------


def test_route_paginates(client):
    resp = client.post(
        "/paginate", json={"items": list(range(10)), "page": 2, "page_size": 3}
    )
    assert resp.status_code == 200
    assert resp.get_json() == {
        "items": [3, 4, 5],
        "page": 2,
        "page_size": 3,
        "total_pages": 4,
    }


def test_route_empty_items_first_page(client):
    resp = client.post("/paginate", json={"items": [], "page": 1, "page_size": 5})
    assert resp.status_code == 200
    assert resp.get_json() == {
        "items": [],
        "page": 1,
        "page_size": 5,
        "total_pages": 1,
    }


def test_route_page_out_of_range(client):
    resp = client.post("/paginate", json={"items": [1, 2], "page": 2, "page_size": 5})
    assert resp.status_code == 400
    assert resp.get_json()["error"] == "invalid pagination request"


def test_route_missing_keys(client):
    resp = client.post("/paginate", json={"page": 1, "page_size": 1})
    assert resp.status_code == 400
    assert resp.get_json()["error"] == "invalid pagination request"


def test_route_non_positive_values(client):
    resp = client.post("/paginate", json={"items": [1], "page": 0, "page_size": 1})
    assert resp.status_code == 400
    assert resp.get_json()["error"] == "invalid pagination request"


def test_route_malformed_json_returns_json_400(client):
    resp = client.post("/paginate", data="{not json", content_type="application/json")
    assert resp.status_code == 400
    assert resp.is_json
    assert resp.get_json()["error"] == "invalid pagination request"


def test_route_missing_body_returns_json_400(client):
    resp = client.post("/paginate")  # no body, no content type
    assert resp.status_code == 400
    assert resp.is_json
    assert resp.get_json()["error"] == "invalid pagination request"


def test_route_wrong_content_type_returns_json_400(client):
    resp = client.post(
        "/paginate",
        data=json.dumps({"items": [], "page": 1, "page_size": 1}),
        content_type="text/plain",
    )
    assert resp.status_code == 400
    assert resp.is_json
    assert resp.get_json()["error"] == "invalid pagination request"


def test_route_non_object_json_body(client):
    resp = client.post("/paginate", json=[1, 2, 3])
    assert resp.status_code == 400
    assert resp.get_json()["error"] == "invalid pagination request"


def test_route_string_items_rejected(client):
    resp = client.post("/paginate", json={"items": "hello", "page": 1, "page_size": 2})
    assert resp.status_code == 400
    assert resp.get_json()["error"] == "invalid pagination request"


def test_route_boolean_page_rejected(client):
    resp = client.post("/paginate", json={"items": [1], "page": True, "page_size": 1})
    assert resp.status_code == 400
    assert resp.get_json()["error"] == "invalid pagination request"


def test_route_float_page_rejected(client):
    resp = client.post(
        "/paginate", json={"items": [1, 2, 3], "page": 1.0, "page_size": 2}
    )
    assert resp.status_code == 400
