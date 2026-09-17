"""Regression tests for GET /todos/<id> (and DELETE, for parity)."""
import pytest

from app import create_app


@pytest.fixture()
def client():
    app = create_app()
    app.config["TESTING"] = True
    with app.test_client() as client:
        yield client


def test_get_todo_by_id_returns_matching_todo(client):
    resp = client.get("/todos/1")
    assert resp.status_code == 200
    assert resp.get_json()["id"] == 1
    assert resp.get_json()["title"] == "write tests"

    resp = client.get("/todos/2")
    assert resp.status_code == 200
    assert resp.get_json()["id"] == 2
    assert resp.get_json()["title"] == "review results"


def test_get_todo_by_id_returns_404_for_unknown_id(client):
    resp = client.get("/todos/999")
    assert resp.status_code == 404
    assert resp.get_json() == {"error": "no such todo"}


def test_delete_todo_by_id(client):
    resp = client.delete("/todos/1")
    assert resp.status_code == 204
    assert client.get("/todos/1").status_code == 404
    assert client.get("/todos/2").status_code == 200
