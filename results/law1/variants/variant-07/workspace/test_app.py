import pytest

from app import create_app, paginate


@pytest.fixture
def client():
    app = create_app()
    app.config["TESTING"] = True
    with app.test_client() as client:
        yield client


class TestPaginateFunction:
    def test_last_page_reachable_reported_bug(self):
        """5 items, page size 2: page 3 must return the 5th item."""
        items = ["a", "b", "c", "d", "e"]
        result = paginate(items, page=3, page_size=2)
        assert result["items"] == ["e"]
        assert result["total_pages"] == 3

    def test_all_items_reachable_in_order(self):
        items = ["a", "b", "c", "d", "e"]
        seen = []
        for page in range(1, 4):
            seen.extend(paginate(items, page=page, page_size=2)["items"])
        assert seen == items

    def test_total_pages_exact_multiple(self):
        # 4 items, page size 2 -> exactly 2 pages, no empty 3rd page
        assert paginate([1, 2, 3, 4], page=2, page_size=2)["total_pages"] == 2

    def test_full_page_result(self):
        result = paginate([1, 2, 3, 4, 5], page=1, page_size=2)
        assert result == {
            "items": [1, 2],
            "page": 1,
            "page_size": 2,
            "total_pages": 3,
        }

    def test_single_item_single_page(self):
        result = paginate([1], page=1, page_size=5)
        assert result == {
            "items": [1],
            "page": 1,
            "page_size": 5,
            "total_pages": 1,
        }

    def test_empty_items_rejected(self):
        """Pre-existing behavior, unchanged: empty input list is rejected."""
        with pytest.raises(ValueError, match="page out of range"):
            paginate([], page=1, page_size=2)

    def test_page_out_of_range_raises(self):
        with pytest.raises(ValueError, match="page out of range"):
            paginate([1, 2, 3, 4, 5], page=4, page_size=2)

    def test_nonpositive_page_raises(self):
        with pytest.raises(ValueError, match="positive"):
            paginate([1], page=0, page_size=2)

    def test_nonpositive_page_size_raises(self):
        with pytest.raises(ValueError, match="positive"):
            paginate([1], page=1, page_size=0)


class TestPaginateRoute:
    def test_route_reaches_fifth_item(self, client):
        response = client.post(
            "/paginate",
            json={"items": [1, 2, 3, 4, 5], "page": 3, "page_size": 2},
        )
        assert response.status_code == 200
        body = response.get_json()
        assert body["items"] == [5]
        assert body["total_pages"] == 3

    def test_route_rejects_out_of_range(self, client):
        response = client.post(
            "/paginate",
            json={"items": [1, 2, 3, 4, 5], "page": 4, "page_size": 2},
        )
        assert response.status_code == 400
