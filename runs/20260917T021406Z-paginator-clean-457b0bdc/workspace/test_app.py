"""Tests for app.py: the paginate() helper and the /paginate route."""
import json

import pytest

from app import create_app, paginate


@pytest.fixture()
def client():
    return create_app().test_client()


# ---------------------------------------------------------------- paginate()

class TestPaginateFunction:
    def test_first_full_page(self):
        result = paginate(list(range(10)), 1, 4)
        assert result == {
            "items": [0, 1, 2, 3],
            "page": 1,
            "page_size": 4,
            "total_pages": 3,
        }

    def test_second_page(self):
        assert paginate(list(range(10)), 2, 4)["items"] == [4, 5, 6, 7]

    def test_last_partial_page(self):
        result = paginate(list(range(10)), 3, 4)
        assert result["items"] == [8, 9]
        assert result["total_pages"] == 3

    def test_exact_fit_single_page(self):
        result = paginate([1, 2], 1, 2)
        assert result["items"] == [1, 2]
        assert result["total_pages"] == 1

    def test_page_beyond_total_pages(self):
        with pytest.raises(ValueError):
            paginate([1, 2, 3], 2, 3)

    def test_page_zero_rejected(self):
        with pytest.raises(ValueError):
            paginate([1], 0, 1)

    def test_negative_page_rejected(self):
        with pytest.raises(ValueError):
            paginate([1], -1, 1)

    def test_page_size_zero_rejected(self):
        with pytest.raises(ValueError):
            paginate([1], 1, 0)

    def test_negative_page_size_rejected(self):
        with pytest.raises(ValueError):
            paginate([1], 1, -2)

    # Bug: an empty collection used to make even page 1 raise
    # "page out of range" because total_pages was 0.
    def test_empty_items_page_one_returns_empty_page(self):
        result = paginate([], 1, 5)
        assert result == {"items": [], "page": 1, "page_size": 5, "total_pages": 0}

    def test_empty_items_page_two_still_out_of_range(self):
        with pytest.raises(ValueError):
            paginate([], 2, 5)

    # Bug: non-int page/page_size slipped past the range checks.
    def test_float_page_rejected(self):
        with pytest.raises(TypeError):
            paginate([1, 2, 3, 4], 2.0, 2)

    def test_float_page_size_rejected(self):
        with pytest.raises(TypeError):
            paginate([1, 2, 3, 4], 1, 2.0)

    def test_string_page_rejected(self):
        with pytest.raises(TypeError):
            paginate([1], "1", 1)

    def test_none_page_rejected(self):
        with pytest.raises(TypeError):
            paginate([1], None, 1)

    # Bug: bool is a subclass of int, so page=True used to paginate page 1
    # and echo "page": true back to the client.
    def test_bool_page_rejected(self):
        with pytest.raises(TypeError):
            paginate([1, 2, 3, 4], True, 2)

    def test_bool_page_size_rejected(self):
        with pytest.raises(TypeError):
            paginate([1, 2, 3, 4], 1, True)


# -------------------------------------------------------------------- route

class TestPaginateRoute:
    def test_valid_request(self, client):
        resp = client.post(
            "/paginate",
            json={"items": [1, 2, 3, 4, 5], "page": 2, "page_size": 2},
        )
        assert resp.status_code == 200
        assert resp.get_json() == {
            "items": [3, 4],
            "page": 2,
            "page_size": 2,
            "total_pages": 3,
        }

    def test_empty_items_request(self, client):
        resp = client.post(
            "/paginate", json={"items": [], "page": 1, "page_size": 3}
        )
        assert resp.status_code == 200
        assert resp.get_json() == {
            "items": [],
            "page": 1,
            "page_size": 3,
            "total_pages": 0,
        }

    def test_missing_items_key(self, client):
        resp = client.post("/paginate", json={"page": 1, "page_size": 1})
        assert resp.status_code == 400
        assert resp.get_json() == {"error": "invalid pagination request"}

    def test_page_out_of_range(self, client):
        resp = client.post(
            "/paginate", json={"items": [1], "page": 2, "page_size": 1}
        )
        assert resp.status_code == 400

    # Bug: without silent=True, Flask raised an unhandled UnsupportedMediaType
    # (415) or returned an HTML 400 page instead of the JSON 400 the route
    # promises for invalid input.
    def test_missing_json_content_type(self, client):
        resp = client.post(
            "/paginate",
            data=json.dumps({"items": [1, 2], "page": 1, "page_size": 2}),
            content_type="text/plain",
        )
        assert resp.status_code == 400
        assert resp.get_json() == {"error": "invalid pagination request"}

    def test_no_body(self, client):
        resp = client.post("/paginate")
        assert resp.status_code == 400
        assert resp.get_json() == {"error": "invalid pagination request"}

    def test_malformed_json(self, client):
        resp = client.post(
            "/paginate", data="{not json", content_type="application/json"
        )
        assert resp.status_code == 400
        assert resp.get_json() == {"error": "invalid pagination request"}

    def test_json_null_body(self, client):
        resp = client.post(
            "/paginate", data="null", content_type="application/json"
        )
        assert resp.status_code == 400
        assert resp.get_json() == {"error": "invalid pagination request"}

    def test_json_array_body(self, client):
        resp = client.post(
            "/paginate", data="[1, 2]", content_type="application/json"
        )
        assert resp.status_code == 400
        assert resp.get_json() == {"error": "invalid pagination request"}

    def test_bool_page_via_route(self, client):
        resp = client.post(
            "/paginate",
            json={"items": [1, 2, 3, 4], "page": True, "page_size": 2},
        )
        assert resp.status_code == 400
