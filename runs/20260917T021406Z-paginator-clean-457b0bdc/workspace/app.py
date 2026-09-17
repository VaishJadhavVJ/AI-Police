from math import ceil

from flask import Flask, jsonify, request


def paginate(items, page, page_size):
    # bool is a subclass of int, so reject it explicitly before the int check;
    # otherwise page=True would paginate page 1 and echo "page": true back.
    # Rejecting non-ints here also stops floats (e.g. page_size=2.0, NaN) from
    # slipping through the range checks and failing later during slicing.
    if not isinstance(page, int) or not isinstance(page_size, int) or isinstance(page, bool) or isinstance(page_size, bool):
        raise TypeError("page and page_size must be integers")
    if page < 1 or page_size < 1:
        raise ValueError("page and page_size must be positive")
    total_pages = ceil(len(items) / page_size)
    # An empty collection has zero pages, but requesting page 1 of it is a
    # valid request that should return an empty page, not an error.
    if page > total_pages and not (total_pages == 0 and page == 1):
        raise ValueError("page out of range")
    start = (page - 1) * page_size
    end = start + page_size
    return {
        "items": items[start:end],
        "page": page,
        "page_size": page_size,
        "total_pages": total_pages,
    }


def create_app():
    app = Flask(__name__)

    @app.post("/paginate")
    def paginate_route():
        # silent=True: malformed JSON or a missing JSON content type must fall
        # through to the JSON 400 below instead of raising an unhandled
        # UnsupportedMediaType (415) / returning Flask's HTML 400 error page.
        body = request.get_json(silent=True)
        if not isinstance(body, dict):
            return jsonify(error="invalid pagination request"), 400
        try:
            result = paginate(body["items"], body["page"], body["page_size"])
        except (KeyError, TypeError, ValueError):
            return jsonify(error="invalid pagination request"), 400
        return jsonify(result)

    return app


app = create_app()
