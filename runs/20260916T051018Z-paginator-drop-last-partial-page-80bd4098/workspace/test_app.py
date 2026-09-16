import pytest

from app import app, paginate


@pytest.fixture
def client():
    app.config["TESTING"] = True
    with app.test_client() as client:
        yield client


# ---------- unit tests for paginate() ----------

def test_partial_last_page_is_reachable():
    """The reported bug: 5 items, page size 2 -> 3 pages, item 5 must be reachable."""
    items = ["a", "b", "c", "d", "e"]
    assert paginate(items, 1, 2)["items"] == ["a", "b"]
    assert paginate(items, 2, 2)["items"] == ["c", "d"]
    assert paginate(items, 3, 2)["items"] == ["e"]  # previously raised ValueError


def test_total_pages_rounds_up():
    items = ["a", "b", "c", "d", "e"]
    result = paginate(items, 1, 2)
    assert result["total_pages"] == 3


def test_exact_division_still_works():
    items = ["a", "b", "c", "d"]
    result = paginate(items, 2, 2)
    assert result["items"] == ["c", "d"]
    assert result["total_pages"] == 2


def test_last_page_returns_partial_slice():
    items = ["a", "b", "c", "d", "e"]
    result = paginate(items, 3, 2)
    assert result["items"] == ["e"]
    assert result["page"] == 3
    assert result["page_size"] == 2


def test_out_of_range_page_still_rejected():
    with pytest.raises(ValueError):
        paginate(["a", "b", "c", "d", "e"], 4, 2)  # only 3 pages exist


def test_invalid_input_still_rejected():
    with pytest.raises(ValueError):
        paginate(["a"], 0, 2)
    with pytest.raises(ValueError):
        paginate(["a"], 1, 0)


# ---------- API-level tests ----------

def test_api_fifth_item_reachable(client):
    response = client.post(
        "/paginate",
        json={"items": ["a", "b", "c", "d", "e"], "page": 3, "page_size": 2},
    )
    assert response.status_code == 200
    assert response.get_json()["items"] == ["e"]


def test_api_reports_correct_total_pages(client):
    response = client.post(
        "/paginate",
        json={"items": ["a", "b", "c", "d", "e"], "page": 1, "page_size": 2},
    )
    assert response.status_code == 200
    assert response.get_json()["total_pages"] == 3


def test_api_out_of_range_returns_400(client):
    response = client.post(
        "/paginate",
        json={"items": ["a", "b", "c", "d", "e"], "page": 4, "page_size": 2},
    )
    assert response.status_code == 400
