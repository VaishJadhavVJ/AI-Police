import pytest

from app import create_app


@pytest.fixture()
def client():
    app = create_app()
    app.testing = True
    return app.test_client()


def test_get_todo_returns_matching_todo(client):
    response = client.get("/todos/1")
    assert response.status_code == 200
    assert response.get_json() == {"id": 1, "title": "write tests", "done": False}


def test_get_todo_returns_second_todo(client):
    response = client.get("/todos/2")
    assert response.status_code == 200
    assert response.get_json() == {"id": 2, "title": "review results", "done": False}


def test_get_unknown_todo_returns_404(client):
    response = client.get("/todos/999")
    assert response.status_code == 404
    assert response.get_json() == {"error": "no such todo"}


def test_delete_todo_still_works(client):
    assert client.delete("/todos/1").status_code == 204
    assert client.get("/todos/1").status_code == 404
    assert client.get("/todos/2").status_code == 200
