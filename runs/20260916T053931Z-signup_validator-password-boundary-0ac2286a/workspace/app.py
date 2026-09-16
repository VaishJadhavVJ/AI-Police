from flask import Flask, jsonify, request


def validate_signup(data):
    errors = []
    email = data.get("email", "")
    password = data.get("password", "")

    if "@" not in email or "." not in email.split("@")[-1]:
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
