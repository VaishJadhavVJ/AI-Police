import pytest

from app import create_app, paginate


@pytest.fixture()
def client():
    app = create_app()
    app.testing = True
    return app.test_client()


def post_json(client, payload):
    return client.post("/paginate", json=payload)


# ---------- unit tests for paginate() ----------


def test_first_page():
    result = paginate(list(range(10)), 1, 4)
    assert result == {
        "items": [0, 1, 2, 3],
        "page": 1,
        "page_size": 4,
        "total_pages": 3,
    }


def test_middle_page():
    assert paginate(list(range(10)), 2, 4)["items"] == [4, 5, 6, 7]


def test_last_partial_page():
    result = paginate(list(range(10)), 3, 4)
    assert result["items"] == [8, 9]
    assert result["total_pages"] == 3


def test_exact_multiple_no_extra_page():
    result = paginate(list(range(8)), 2, 4)
    assert result["items"] == [4, 5, 6, 7]
    assert result["total_pages"] == 2


def test_total_pages_is_an_int():
    assert isinstance(paginate(list(range(10)), 1, 4)["total_pages"], int)


def test_rejects_zero_page():
    with pytest.raises(ValueError):
        paginate([1, 2], 0, 1)


def test_rejects_negative_page_size():
    with pytest.raises(ValueError):
        paginate([1, 2], 1, -2)


def test_rejects_page_beyond_last():
    with pytest.raises(ValueError):
        paginate(list(range(8)), 3, 4)


def test_empty_items_page_one_is_valid():
    result = paginate([], 1, 5)
    assert result["items"] == []
    assert result["total_pages"] == 1


def test_empty_items_page_two_is_out_of_range():
    with pytest.raises(ValueError):
        paginate([], 2, 5)


# ---------- API tests ----------


def test_api_happy_path(client):
    resp = post_json(client, {"items": list(range(10)), "page": 2, "page_size": 4})
    assert resp.status_code == 200
    assert resp.get_json() == {
        "items": [4, 5, 6, 7],
        "page": 2,
        "page_size": 4,
        "total_pages": 3,
    }


def test_api_empty_items_returns_empty_page(client):
    resp = post_json(client, {"items": [], "page": 1, "page_size": 5})
    assert resp.status_code == 200
    body = resp.get_json()
    assert body["items"] == []
    assert body["total_pages"] == 1


def test_api_page_out_of_range(client):
    resp = post_json(client, {"items": [1, 2, 3], "page": 9, "page_size": 2})
    assert resp.status_code == 400
    assert resp.is_json and "error" in resp.get_json()


def test_api_missing_field(client):
    resp = post_json(client, {"items": [1], "page": 1})
    assert resp.status_code == 400


def test_api_non_integer_page(client):
    resp = post_json(client, {"items": [1], "page": "1", "page_size": 1})
    assert resp.status_code == 400


def test_api_zero_page_size(client):
    resp = post_json(client, {"items": [1], "page": 1, "page_size": 0})
    assert resp.status_code == 400


def test_api_non_json_body(client):
    resp = client.post("/paginate", data="not json", content_type="text/plain")
    assert resp.status_code == 400
    assert resp.is_json


def test_api_json_body_is_not_an_object(client):
    resp = client.post("/paginate", json=[1, 2, 3])
    assert resp.status_code == 400
