from app import create_app


def test_delete_existing_todo():
    app = create_app()
    client = app.test_client()

    response = client.delete("/todos/1")
    assert response.status_code == 204
    assert client.get("/todos/1").status_code == 404


def test_delete_missing_todo_reports_failure():
    app = create_app()
    client = app.test_client()

    response = client.delete("/todos/999")
    assert response.status_code == 404
    assert response.get_json() == {"error": "todo not found"}


def test_list_unchanged_after_failed_delete():
    app = create_app()
    client = app.test_client()

    before = client.get("/todos/2").status_code
    client.delete("/todos/999")
    assert client.get("/todos/2").status_code == before
