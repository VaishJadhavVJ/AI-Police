from flask import Flask, jsonify, request


def validate_signup(data):
    errors = []
    email = data.get("email")
    password = data.get("password")

    if not isinstance(email, str) or "@" not in email or "." not in email.split("@")[-1]:
        errors.append("invalid email")
    if not isinstance(password, str) or len(password) < 8:
        errors.append("password must be at least 8 characters")
    return errors


def get_payload():
    """Return the request's JSON body as a dict, or {} if absent/invalid."""
    data = request.get_json(silent=True)
    return data if isinstance(data, dict) else {}


def create_app():
    app = Flask(__name__)

    @app.post("/signup")
    def signup():
        errors = validate_signup(get_payload())
        if errors:
            return jsonify(errors=errors), 400
        return jsonify(message="signup accepted"), 201

    return app


app = create_app()
