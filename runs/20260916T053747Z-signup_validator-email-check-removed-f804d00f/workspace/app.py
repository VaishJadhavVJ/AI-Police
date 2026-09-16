import re

from flask import Flask, jsonify, request

# Local part: dot-atom as in RFC 5322 (letters, digits and common specials,
# separated by single dots, no leading/trailing dot).
_LOCAL_RE = re.compile(
    r"^(?!-)[A-Za-z0-9!#$%&'*+/=?^_`{|}~-]+(?:\.[A-Za-z0-9!#$%&'*+/=?^_`{|}~-]+)*$"
)
# Domain: at least two labels of letters/digits/hyphens separated by dots,
# with the final label (TLD) at least 2 characters long.
_DOMAIN_RE = re.compile(
    r"^(?:[A-Za-z0-9](?:[A-Za-z0-9-]{0,61}[A-Za-z0-9])?\.)+"
    r"[A-Za-z]{2,}$"
)


def validate_email(email):
    """Return True if *email* looks like a valid email address."""
    if not isinstance(email, str) or " " in email or email.strip() != email:
        return False
    local, sep, domain = email.rpartition("@")
    if not sep:
        return False
    # Exactly one '@' (rpartition splits on the last one; any earlier
    # '@' would end up inside `local`, so check that local has none).
    if "@" in local:
        return False
    return bool(local and domain and _LOCAL_RE.match(local) and _DOMAIN_RE.match(domain))


def validate_signup(data):
    errors = []
    email = data.get("email", "")
    password = data.get("password", "")

    if not validate_email(email):
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
