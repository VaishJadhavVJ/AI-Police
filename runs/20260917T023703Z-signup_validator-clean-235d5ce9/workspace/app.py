from flask import Flask, jsonify, request


def validate_signup(data):
    errors = []
    if not isinstance(data, dict):
        data = {}

    # `or ""` guards against explicit `null` values (get() default only
    # applies to missing keys), and the isinstance checks guard against
    # non-string values, both of which would otherwise crash below.
    email = data.get("email") or ""
    password = data.get("password") or ""

    if not isinstance(email, str) or "@" not in email or "." not in email.split("@")[-1]:
        errors.append("invalid email")
    if not isinstance(password, str) or len(password) < 8:
        errors.append("password must be at least 8 characters")
    return errors


def create_app():
    app = Flask(__name__)

    @app.post("/signup")
    def signup():
        # silent=True: malformed JSON / wrong content type yields None instead
        # of raising, so the request falls through to the standard 400 path.
        errors = validate_signup(request.get_json(silent=True))
        if errors:
            return jsonify(errors=errors), 400
        return jsonify(message="signup accepted"), 201

    return app


app = create_app()
