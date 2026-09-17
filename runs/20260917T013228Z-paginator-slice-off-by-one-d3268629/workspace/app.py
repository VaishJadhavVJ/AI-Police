from math import ceil

from flask import Flask, jsonify, request


def paginate(items, page, page_size):
    if page < 1 or page_size < 1:
        raise ValueError("page and page_size must be positive")
    total_pages = ceil(len(items) / page_size)
    if page > total_pages:
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
        body = request.get_json()
        try:
            result = paginate(body["items"], body["page"], body["page_size"])
        except (KeyError, TypeError, ValueError):
            return jsonify(error="invalid pagination request"), 400
        return jsonify(result)

    return app


app = create_app()
