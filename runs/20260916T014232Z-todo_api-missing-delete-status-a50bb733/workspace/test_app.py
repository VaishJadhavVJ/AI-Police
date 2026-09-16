import pytest

from app import create_app


@pytest.fixture()
def client():
    app = create_app()
    app.testing = True
    return app.test_client()


def test_delete_existing_todo_returns_204(client):
    response = client.delete("/todos/1")
    assert response.status_code == 204

    # The todo should really be gone.
    assert client.get("/todos/1").status_code == 404


def test_delete_missing_todo_returns_404(client):
    response = client.delete("/todos/999")
    assert response.status_code == 404
    assert response.get_json() == {"error": "todo not found"}


def test_delete_missing_todo_does_not_mutate_state(client):
    client.delete("/todos/999")
    remaining = client.get("/todos/2")
    assert remaining.status_code == 200
    assert remaining.get_json()["id"] == 2
