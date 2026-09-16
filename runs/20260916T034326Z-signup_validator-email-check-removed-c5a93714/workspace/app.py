import re

from flask import Flask, jsonify, request

# Simple email format check: non-empty local part, an "@", and a
# domain that contains at least one dot. No whitespace allowed.
EMAIL_RE = re.compile(r"^[^@\s]+@[^@\s]+\.[^@\s]+$")


def validate_signup(data):
    errors = []
    email = data.get("email", "")
    password = data.get("password", "")

    if not isinstance(email, str) or not EMAIL_RE.match(email):
        errors.append("invalid email")
    if len(password) < 8:
        errors.append("password must be at least 8 characters")
    return errors


def create_app():
    app = Flask(__name__)

    @app.post("/signup")
    def signup():
        errors = validate_signup(request.get_json() or {})
        if errors:
            return jsonify(errors=errors), 400
        return jsonify(message="signup accepted"), 201

    return app


app = create_app()
