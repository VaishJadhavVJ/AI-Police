from flask import Flask, jsonify, request


def validate_signup(data):
    errors = []
    email = data.get("email", "")
    password = data.get("password", "")

    if not isinstance(email, str):
        errors.append("invalid email")
    elif "@" not in email or "." not in email.split("@")[-1]:
        errors.append("invalid email")
    if not isinstance(password, str) or len(password) < 8:
        errors.append("password must be at least 8 characters")
    return errors


def create_app():
    app = Flask(__name__)

    @app.post("/signup")
    def signup():
        # get_json(silent=True) returns None instead of raising for a
        # missing/incorrect Content-Type or malformed JSON.
        payload = request.get_json(silent=True)
        if not isinstance(payload, dict):
            return jsonify(errors=["request body must be a JSON object"]), 400
        errors = validate_signup(payload)
        if errors:
            return jsonify(errors=errors), 400
        return jsonify(message="signup accepted"), 201

    return app


app = create_app()
