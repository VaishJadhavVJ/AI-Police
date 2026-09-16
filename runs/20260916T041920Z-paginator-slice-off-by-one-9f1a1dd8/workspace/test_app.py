import pytest

from app import create_app, paginate


ITEMS = list(range(1, 11))  # [1..10]


class TestPaginateUnit:
    def test_first_page_includes_first_item(self):
        assert paginate(ITEMS, 1, 4)["items"] == [1, 2, 3, 4]

    def test_second_page(self):
        assert paginate(ITEMS, 2, 4)["items"] == [5, 6, 7, 8]

    def test_last_partial_page(self):
        assert paginate(ITEMS, 3, 4)["items"] == [9, 10]

    def test_no_item_lost_across_all_pages(self):
        seen = []
        for page in range(1, 4):
            seen.extend(paginate(ITEMS, page, 4)["items"])
        assert seen == ITEMS

    def test_pages_are_contiguous_no_overlap(self):
        seen = []
        for page in range(1, 4):
            seen.extend(paginate(ITEMS, page, 4)["items"])
        assert len(seen) == len(set(seen))

    def test_metadata(self):
        result = paginate(ITEMS, 2, 4)
        assert result["page"] == 2
        assert result["page_size"] == 4
        assert result["total_pages"] == 3

    def test_exact_multiple_page_size(self):
        assert paginate(ITEMS, 2, 5)["items"] == [6, 7, 8, 9, 10]

    def test_page_size_larger_than_items(self):
        result = paginate(ITEMS, 1, 100)
        assert result["items"] == ITEMS
        assert result["total_pages"] == 1

    @pytest.mark.parametrize("page,page_size", [(0, 4), (-1, 4), (1, 0), (1, -2)])
    def test_invalid_arguments_raise(self, page, page_size):
        with pytest.raises(ValueError):
            paginate(ITEMS, page, page_size)

    def test_page_out_of_range_raises(self):
        with pytest.raises(ValueError):
            paginate(ITEMS, 4, 4)


@pytest.fixture()
def client():
    return create_app().test_client()


class TestPaginateRoute:
    def post(self, client, items=ITEMS, page=1, page_size=4):
        return client.post(
            "/paginate",
            json={"items": items, "page": page, "page_size": page_size},
        )

    def test_first_page_returns_first_item(self, client):
        resp = self.post(client)
        assert resp.status_code == 200
        assert resp.get_json()["items"] == [1, 2, 3, 4]

    def test_all_items_retrievable_via_api(self, client):
        seen = []
        for page in (1, 2, 3):
            resp = self.post(client, page=page)
            assert resp.status_code == 200
            seen.extend(resp.get_json()["items"])
        assert seen == ITEMS

    def test_invalid_request_returns_400(self, client):
        resp = self.post(client, page=0)
        assert resp.status_code == 400
        assert "error" in resp.get_json()

    def test_page_out_of_range_returns_400(self, client):
        assert self.post(client, page=99).status_code == 400
