from flask import Flask, jsonify


INITIAL_TODOS = [
    {"id": 1, "title": "write tests", "done": False},
    {"id": 2, "title": "review results", "done": False},
]


def create_app():
    app = Flask(__name__)
    app.config["TODOS"] = [todo.copy() for todo in INITIAL_TODOS]

    @app.get("/todos/<int:todo_id>")
    def get_todo(todo_id):
        todo = next(
            (todo for todo in app.config["TODOS"] if todo["id"] == todo_id),
            None,
        )
        if todo is None:
            return jsonify(error="no such todo"), 404
        return jsonify(todo)

    @app.delete("/todos/<int:todo_id>")
    def delete_todo(todo_id):
        todos = app.config["TODOS"]
        for index, todo in enumerate(todos):
            if todo["id"] == todo_id:
                todos.pop(index)
                return "", 204
        return jsonify(error="todo not found"), 200

    return app


app = create_app()