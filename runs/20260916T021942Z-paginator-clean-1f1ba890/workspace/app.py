from math import ceil

from flask import Flask, jsonify, request


def _as_positive_int(value):
    """Return *value* if it is a true positive integer, else raise TypeError.

    bool is excluded explicitly because bool is a subclass of int, and
    True/False must not be silently treated as 1/0.
    """
    if isinstance(value, bool) or not isinstance(value, int):
        raise TypeError("expected an integer")
    if value < 1:
        raise ValueError("page and page_size must be positive")
    return value


def paginate(items, page, page_size):
    # Accept only real sequences of items: str/bytes would otherwise be sliced
    # into characters/bytes and returned as bogus "items", and None/int/dict
    # would crash here instead of surfacing as a clean 400 at the endpoint.
    if isinstance(items, (str, bytes, bytearray)) or not isinstance(items, (list, tuple)):
        raise TypeError("items should be a list")

    _as_positive_int(page)
    _as_positive_int(page_size)

    # An empty collection still has one (empty) page, so page 1 stays valid;
    # any non-empty list with page_size >= 1 already yields ceil(...) >= 1.
    total_pages = max(1, ceil(len(items) / page_size))
    if page > total_pages:
        raise ValueError("page out of range")

    start = (page - 1) * page_size
    end = start + page_size
    return {
        "items": list(items[start:end]),
        "page": page,
        "page_size": page_size,
        "total_pages": total_pages,
    }


def create_app():
    app = Flask(__name__)

    @app.post("/paginate")
    def paginate_route():
        try:
            # silent=True: missing/malformed/non-JSON bodies yield None here so
            # they are handled below as a 400 with our JSON error contract,
            # instead of Flask's default HTML error page.
            body = request.get_json(silent=True)
            if not isinstance(body, dict):
                raise TypeError("expected a JSON object")
            result = paginate(body["items"], body["page"], body["page_size"])
        except (KeyError, TypeError, ValueError):
            return jsonify(error="invalid pagination request"), 400
        return jsonify(result)

    return app


app = create_app()
