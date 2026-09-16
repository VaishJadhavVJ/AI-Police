import pytest

from app import create_app, paginate

ITEMS = ["a", "b", "c", "d", "e", "f", "g"]  # 7 items


# ---------- paginate() unit tests ----------


def test_first_item_appears_on_page_one():
    result = paginate(ITEMS, 1, 3)
    assert result["items"][0] == "a"


def test_no_items_skipped_or_duplicated_across_pages():
    collected = []
    for page in range(1, 4):
        collected.extend(paginate(ITEMS, page, 3)["items"])
    assert collected == ITEMS


def test_last_page_is_partial():
    result = paginate(ITEMS, 3, 3)
    assert result["items"] == ["g"]
    assert result["total_pages"] == 3


def test_exact_multiple_of_page_size():
    # 6 items, page_size 3 -> exactly 2 full pages, no empty third page
    assert paginate(ITEMS[:6], 1, 3)["items"] == ["a", "b", "c"]
    assert paginate(ITEMS[:6], 2, 3)["items"] == ["d", "e", "f"]
    assert paginate(ITEMS[:6], 2, 3)["total_pages"] == 2


def test_single_item():
    result = paginate(["only"], 1, 5)
    assert result["items"] == ["only"]
    assert result["total_pages"] == 1


def test_empty_list_has_no_pages():
    # Current (pre-existing) behavior: an empty list has total_pages == 0,
    # so every page request, including page 1, is rejected as out of range.
    with pytest.raises(ValueError):
        paginate([], 1, 3)


def test_page_size_one_pages_one_at_a_time():
    pages = [paginate(ITEMS, p, 1)["items"] for p in range(1, 8)]
    assert pages == [[x] for x in ITEMS]


@pytest.mark.parametrize("page,page_size", [(0, 3), (1, 0), (-1, 3), (1, -3)])
def test_invalid_arguments_raise(page, page_size):
    with pytest.raises(ValueError):
        paginate(ITEMS, page, page_size)


def test_page_out_of_range_raises():
    with pytest.raises(ValueError):
        paginate(ITEMS, 4, 3)


# ---------- HTTP route tests ----------


@pytest.fixture()
def client():
    return create_app().test_client()


def test_route_first_item_on_page_one(client):
    resp = client.post(
        "/paginate", json={"items": ITEMS, "page": 1, "page_size": 3}
    )
    assert resp.status_code == 200
    assert resp.get_json()["items"] == ["a", "b", "c"]


def test_route_invalid_request_returns_400(client):
    resp = client.post("/paginate", json={"items": ITEMS, "page": 0, "page_size": 3})
    assert resp.status_code == 400
    assert "error" in resp.get_json()

    resp = client.post("/paginate", json={"page": 1, "page_size": 3})
    assert resp.status_code == 400


def test_route_paginates_fully(client):
    all_items = []
    page = 1
    while True:
        resp = client.post(
            "/paginate", json={"items": ITEMS, "page": page, "page_size": 3}
        )
        assert resp.status_code == 200
        data = resp.get_json()
        all_items.extend(data["items"])
        if page >= data["total_pages"]:
            break
        page += 1
    assert all_items == ITEMS
