"""Regression suite from the app.py review. app.py itself was left unchanged."""
import pytest

from app import create_app, INITIAL_TODOS


@pytest.fixture()
def client():
    return create_app().test_client()


def test_get_existing_todo(client):
    r = client.get("/todos/1")
    assert r.status_code == 200
    assert r.get_json() == {"id": 1, "title": "write tests", "done": False}


def test_get_missing_todo_is_404_json(client):
    r = client.get("/todos/999")
    assert r.status_code == 404
    assert "error" in r.get_json()


def test_non_integer_id_is_routed_as_404(client):
    assert client.get("/todos/abc").status_code == 404
    assert client.get("/todos/-1").status_code == 404


def test_delete_returns_204_and_removes_todo(client):
    assert client.delete("/todos/1").status_code == 204
    assert client.get("/todos/1").status_code == 404


def test_delete_missing_todo_is_404(client):
    assert client.delete("/todos/42").status_code == 404


def test_delete_is_idempotent_unsafe(client):
    # First delete succeeds; second must 404, not crash or double-pop.
    assert client.delete("/todos/1").status_code == 204
    assert client.delete("/todos/1").status_code == 404


def test_delete_removes_exactly_one_element():
    app = create_app()
    store = app.config["TODOS"]
    app.test_client().delete("/todos/1")
    assert len(store) == 1 and store[0]["id"] == 2


def test_new_app_gets_fresh_store():
    client = create_app().test_client()
    assert client.get("/todos/1").status_code == 200
    assert client.get("/todos/2").status_code == 200


def test_apps_do_not_share_state():
    a, b = create_app(), create_app()
    a.test_client().delete("/todos/1")
    assert b.test_client().get("/todos/1").status_code == 200


def test_initial_todos_not_mutated():
    create_app().test_client().delete("/todos/1")
    assert len(INITIAL_TODOS) == 2
    assert INITIAL_TODOS[0]["title"] == "write tests"
