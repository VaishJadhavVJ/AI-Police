"""Tests for app.py — verify the todo API behaves as intended."""

import pytest

from app import INITIAL_TODOS, create_app


@pytest.fixture()
def client():
    """A fresh app (and client) per test so state never leaks between tests."""
    app = create_app()
    app.testing = True
    return app.test_client()


# --- GET /todos/<id> ---------------------------------------------------------


def test_get_first_todo(client):
    resp = client.get("/todos/1")
    assert resp.status_code == 200
    assert resp.content_type.startswith("application/json")
    assert resp.get_json() == {"id": 1, "title": "write tests", "done": False}


def test_get_second_todo(client):
    resp = client.get("/todos/2")
    assert resp.status_code == 200
    assert resp.get_json() == {"id": 2, "title": "review results", "done": False}


def test_get_missing_todo_is_404_json(client):
    resp = client.get("/todos/999")
    assert resp.status_code == 404
    assert resp.get_json() == {"error": "no such todo"}


def test_get_non_integer_id_is_routed_to_404(client):
    assert client.get("/todos/abc").status_code == 404


# --- DELETE /todos/<id> ------------------------------------------------------


def test_delete_existing_todo(client):
    resp = client.delete("/todos/1")
    assert resp.status_code == 204
    assert resp.data == b""
    # The deleted todo is gone...
    assert client.get("/todos/1").status_code == 404
    # ...and the other todo is untouched.
    assert client.get("/todos/2").status_code == 200


def test_delete_missing_todo_is_404_json(client):
    resp = client.delete("/todos/999")
    assert resp.status_code == 404
    assert resp.get_json() == {"error": "todo not found"}


def test_deleting_the_same_todo_twice(client):
    assert client.delete("/todos/2").status_code == 204
    resp = client.delete("/todos/2")
    assert resp.status_code == 404
    assert resp.get_json() == {"error": "todo not found"}


def test_can_delete_all_todos(client):
    assert client.delete("/todos/2").status_code == 204
    assert client.delete("/todos/1").status_code == 204
    assert client.get("/todos/1").status_code == 404
    assert client.get("/todos/2").status_code == 404


# --- State isolation ---------------------------------------------------------


def test_separate_apps_do_not_share_state():
    app1, app2 = create_app(), create_app()
    assert app1.test_client().delete("/todos/1").status_code == 204
    assert app1.test_client().get("/todos/1").status_code == 404
    assert app2.test_client().get("/todos/1").status_code == 200


def test_module_level_initial_todos_are_not_mutated(client):
    client.delete("/todos/1")
    assert INITIAL_TODOS == [
        {"id": 1, "title": "write tests", "done": False},
        {"id": 2, "title": "review results", "done": False},
    ]
