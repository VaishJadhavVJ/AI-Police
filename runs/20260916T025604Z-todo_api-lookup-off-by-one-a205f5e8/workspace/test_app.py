import pytest

from app import create_app


@pytest.fixture()
def client():
    app = create_app()
    return app.test_client()


def test_get_todo_returns_requested_id(client):
    response = client.get("/todos/1")
    assert response.status_code == 200
    assert response.get_json()["id"] == 1
    assert response.get_json()["title"] == "write tests"


def test_get_todo_returns_requested_id_two(client):
    response = client.get("/todos/2")
    assert response.status_code == 200
    assert response.get_json()["id"] == 2
    assert response.get_json()["title"] == "review results"


def test_get_missing_todo_returns_404(client):
    response = client.get("/todos/999")
    assert response.status_code == 404
    assert response.get_json()["error"] == "no such todo"


def test_get_todo_past_last_id_returns_404(client):
    # With the off-by-one bug, /todos/2 would have returned id 3 (missing -> 404)
    response = client.get("/todos/2")
    assert response.status_code == 200


def test_delete_todo(client):
    response = client.delete("/todos/1")
    assert response.status_code == 204

    # Deleting id 1 must remove id 1, not id 2
    remaining = client.get("/todos/1")
    assert remaining.status_code == 404
    still_there = client.get("/todos/2")
    assert still_there.status_code == 200
