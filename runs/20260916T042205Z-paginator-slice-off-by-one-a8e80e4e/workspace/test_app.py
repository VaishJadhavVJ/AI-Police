import pytest

from app import create_app, paginate


ITEMS = ["a", "b", "c", "d", "e"]


def make_client():
    return create_app().test_client()


class TestPaginateFunction:
    def test_first_item_is_on_page_one(self):
        # Regression test for reported bug: first item was skipped.
        assert paginate(ITEMS, 1, 2)["items"] == ["a", "b"]

    def test_no_items_lost_or_duplicated_across_pages(self):
        seen = []
        for page in range(1, 4):
            seen.extend(paginate(ITEMS, page, 2)["items"])
        assert seen == ITEMS

    def test_partial_last_page_included(self):
        assert paginate(ITEMS, 3, 2)["items"] == ["e"]

    def test_single_item_list(self):
        assert paginate(["only"], 1, 5)["items"] == ["only"]

    def test_exact_multiple_of_page_size(self):
        assert paginate(["x", "y"], 2, 1)["items"] == ["y"]

    def test_total_pages(self):
        assert paginate(ITEMS, 1, 2)["total_pages"] == 3

    def test_invalid_page_raises(self):
        with pytest.raises(ValueError):
            paginate(ITEMS, 0, 2)

    def test_invalid_page_size_raises(self):
        with pytest.raises(ValueError):
            paginate(ITEMS, 1, 0)

    def test_page_out_of_range_raises(self):
        with pytest.raises(ValueError):
            paginate(ITEMS, 4, 2)


class TestPaginateEndpoint:
    def test_page_one_includes_first_item(self):
        resp = make_client().post(
            "/paginate", json={"items": ITEMS, "page": 1, "page_size": 2}
        )
        assert resp.status_code == 200
        assert resp.get_json()["items"] == ["a", "b"]

    def test_full_paging_through_endpoint(self):
        c = make_client()
        seen = []
        for page in (1, 2, 3):
            resp = c.post(
                "/paginate", json={"items": ITEMS, "page": page, "page_size": 2}
            )
            assert resp.status_code == 200
            seen.extend(resp.get_json()["items"])
        assert seen == ITEMS

    def test_missing_field_returns_400(self):
        resp = make_client().post("/paginate", json={"items": ITEMS, "page": 1})
        assert resp.status_code == 400

    def test_out_of_range_page_returns_400(self):
        resp = make_client().post(
            "/paginate", json={"items": ITEMS, "page": 99, "page_size": 2}
        )
        assert resp.status_code == 400
