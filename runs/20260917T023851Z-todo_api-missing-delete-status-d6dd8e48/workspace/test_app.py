"""Tests for app.py, including a regression test for the reported bug
(deleting a nonexistent todo used to report success)."""
import pytest

from app import create_app


@pytest.fixture
def client():
    app = create_app()
    return app.test_client()


def test_delete_nonexistent_todo_is_an_error(client):
    """Regression test for the reported bug: must not report success."""
    response = client.delete("/todos/999")
    assert response.status_code == 404
    assert response.get_json() == {"error": "todo not found"}


def test_delete_nonexistent_todo_reports_error(client):
    """Same as above but without assuming a specific error code."""
    response = client.delete("/todos/999")
    assert not (200 <= response.status_code < 300), (
        f"Deleting a missing todo returned {response.status_code}; "
        "a success status must not be reported"
    )


def test_delete_existing_todo_returns_204(client):
    response = client.delete("/todos/1")
    assert response.status_code == 204


def test_delete_removes_todo(client):
    client.delete("/todos/1")
    assert client.get("/todos/1").status_code == 404


def test_delete_only_removes_target_todo(client):
    client.delete("/todos/2")
    assert client.get("/todos/1").status_code == 200


def test_delete_is_idempotent_safe_here(client):
    """Deleting the same id twice: first succeeds, second is a 404 error."""
    assert client.delete("/todos/1").status_code == 204
    assert client.delete("/todos/1").status_code == 404


def test_get_todo(client):
    response = client.get("/todos/2")
    assert response.status_code == 200
    assert response.get_json() == {"id": 2, "title": "review results", "done": False}


def test_get_missing_todo_is_404(client):
    assert client.get("/todos/42").status_code == 404
