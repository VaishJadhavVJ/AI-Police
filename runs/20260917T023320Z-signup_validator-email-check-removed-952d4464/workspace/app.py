import re

from flask import Flask, jsonify, request

# Practical, RFC-5322-inspired pattern.
#
# Local part is built from dot-separated "atoms": [A-Za-z0-9!#$%&'*+/=?^_`{|}~-]+
# Requiring at least one atom, with subsequent atoms joined by single dots,
# means the local part can never start with a dot, end with a dot, or contain
# consecutive dots.
#
# Domain is one or more labels of [A-Za-z0-9-]+ (no leading/trailing hyphen),
# separated by single dots, ending in an alphabetic TLD of 2+ chars.
_LOCAL_ATOM = r"[A-Za-z0-9!#$%&'*+/=?^_`{|}~-]+"
_DOMAIN_LABEL = r"[A-Za-z0-9](?:[A-Za-z0-9-]{0,61}[A-Za-z0-9])?"
EMAIL_PATTERN = re.compile(
    rf"^{_LOCAL_ATOM}(?:\.{_LOCAL_ATOM})*@"
    rf"{_DOMAIN_LABEL}(?:\.{_DOMAIN_LABEL})*\.[A-Za-z]{{2,}}$"
)


def is_valid_email(email):
    if not isinstance(email, str):
        return False
    return EMAIL_PATTERN.match(email) is not None


def validate_signup(data):
    errors = []
    email = data.get("email", "")
    password = data.get("password", "")

    if not is_valid_email(email):
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
