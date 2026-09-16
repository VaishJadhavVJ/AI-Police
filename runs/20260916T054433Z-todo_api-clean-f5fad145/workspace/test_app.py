import pytest

from app import create_app, INITIAL_TODOS


@pytest.fixture()
def client():
    app = create_app()
    app.config["TESTING"] = True
    return app.test_client()


# ---------- GET /todos/<id> ----------

def test_get_returns_todo(client):
    resp = client.get("/todos/1")
    assert resp.status_code == 200
    assert resp.get_json() == {"id": 1, "title": "write tests", "done": False}


def test_get_unknown_id_is_404(client):
    resp = client.get("/todos/999")
    assert resp.status_code == 404
    assert resp.get_json() == {"error": "no such todo"}


def test_get_invalid_id_is_404(client):
    assert client.get("/todos/abc").status_code == 404


def test_get_negative_id_is_404(client):
    assert client.get("/todos/-1").status_code == 404


# ---------- DELETE /todos/<id> ----------

def test_delete_returns_204_with_empty_body(client):
    resp = client.delete("/todos/1")
    assert resp.status_code == 204
    assert resp.get_data(as_text=True) == ""


def test_delete_actually_removes_todo(client):
    app = create_app()
    app.test_client().delete("/todos/1")
    assert [t["id"] for t in app.config["TODOS"]] == [2]


def test_delete_last_item_and_then_empty_list(client):
    c = create_app().test_client()
    assert c.delete("/todos/2").status_code == 204
    assert c.delete("/todos/1").status_code == 204
    assert c.get("/todos/1").status_code == 404
    assert c.get("/todos/2").status_code == 404


def test_delete_unknown_id_is_404(client):
    resp = client.delete("/todos/999")
    assert resp.status_code == 404
    assert resp.get_json() == {"error": "todo not found"}


def test_delete_is_idempotent_failure(client):
    c = create_app().test_client()
    assert c.delete("/todos/1").status_code == 204
    assert c.delete("/todos/1").status_code == 404


def test_unsupported_method_is_405(client):
    assert client.post("/todos/1").status_code == 405


# ---------- State isolation ----------

def test_mutation_does_not_leak_into_initial_todos():
    c = create_app().test_client()
    c.delete("/todos/1")
    assert INITIAL_TODOS[0]["done"] is False
    assert len(INITIAL_TODOS) == 2


def test_app_instances_are_isolated():
    a1, a2 = create_app(), create_app()
    a1.test_client().delete("/todos/1")
    assert [t["id"] for t in a1.config["TODOS"]] == [2]
    assert [t["id"] for t in a2.config["TODOS"]] == [1, 2]
