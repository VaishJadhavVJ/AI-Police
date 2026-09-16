import pytest

from app import create_app, paginate


class TestPaginateUnit:
    def test_first_page_returns_zero_based_slice(self):
        items = ["a", "b", "c", "d", "e"]
        result = paginate(items, 1, 3)
        assert result["items"] == ["a", "b", "c"]  # starts at index 0, not 1

    def test_second_page_starts_right_after_first(self):
        items = ["a", "b", "c", "d", "e"]
        result = paginate(items, 2, 3)
        assert result["items"] == ["d", "e"]  # starts at index 3

    def test_pages_are_contiguous_and_cover_all_items(self):
        items = list(range(10))
        collected = []
        for page in range(1, 5):
            collected.extend(paginate(items, page, 3)["items"])
        assert collected == items  # no item skipped or duplicated

    def test_exact_multiple_last_page_full(self):
        items = list(range(9))
        result = paginate(items, 3, 3)
        assert result["items"] == [6, 7, 8]
        assert result["total_pages"] == 3

    def test_single_item_pages(self):
        items = ["x", "y"]
        assert paginate(items, 1, 1)["items"] == ["x"]
        assert paginate(items, 2, 1)["items"] == ["y"]

    def test_page_size_larger_than_list(self):
        result = paginate(["only"], 1, 10)
        assert result["items"] == ["only"]
        assert result["total_pages"] == 1

    def test_empty_list_rejected(self):
        with pytest.raises(ValueError, match="out of range"):
            paginate([], 1, 3)

    def test_metadata(self):
        result = paginate(list(range(7)), 2, 3)
        assert result["page"] == 2
        assert result["page_size"] == 3
        assert result["total_pages"] == 3

    @pytest.mark.parametrize("page,page_size", [(0, 3), (-1, 3), (3, 0), (3, -2)])
    def test_invalid_arguments(self, page, page_size):
        with pytest.raises(ValueError, match="must be positive"):
            paginate(["a"], page, page_size)

    def test_page_out_of_range(self):
        with pytest.raises(ValueError, match="out of range"):
            paginate(["a", "b"], 3, 2)


class TestPaginateRoute:
    @pytest.fixture()
    def client(self):
        return create_app().test_client()

    def test_route_first_page(self, client):
        resp = client.post(
            "/paginate",
            json={"items": [1, 2, 3, 4, 5], "page": 1, "page_size": 2},
        )
        assert resp.status_code == 200
        assert resp.get_json()["items"] == [1, 2]

    def test_route_all_pages_no_gaps(self, client):
        items = list(range(10))
        collected = []
        for page in (1, 2, 3, 4):
            resp = client.post(
                "/paginate", json={"items": items, "page": page, "page_size": 3}
            )
            assert resp.status_code == 200
            collected.extend(resp.get_json()["items"])
        assert collected == items

    def test_route_invalid_page_returns_400(self, client):
        resp = client.post(
            "/paginate", json={"items": [1], "page": 0, "page_size": 2}
        )
        assert resp.status_code == 400
        assert "error" in resp.get_json()

    def test_route_missing_field_returns_400(self, client):
        resp = client.post("/paginate", json={"page": 1, "page_size": 2})
        assert resp.status_code == 400

    def test_route_page_out_of_range_returns_400(self, client):
        resp = client.post(
            "/paginate", json={"items": [1, 2], "page": 5, "page_size": 2}
        )
        assert resp.status_code == 400
