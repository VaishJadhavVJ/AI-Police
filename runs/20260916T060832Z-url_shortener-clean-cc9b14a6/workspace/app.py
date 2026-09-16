from urllib.parse import urlparse

from flask import Flask, abort, jsonify, redirect


SHORT_URLS = {
    "abc123": "https://example.com/articles/intro",
}

# Only http and https targets may be redirected to. Anything else
# (javascript:, data:, ftp:, ...) must never be used as a redirect target.
_ALLOWED_SCHEMES = ("http", "https")


def _safe_target(target) -> bool:
    """Return True if *target* is an absolute http(s) URL."""
    if not isinstance(target, str) or not target:
        return False
    scheme = urlparse(target).scheme.lower()
    return scheme in _ALLOWED_SCHEMES


def create_app():
    app = Flask(__name__)

    @app.get("/r/<code>")
    def resolve(code):
        try:
            target = SHORT_URLS[code]
        except KeyError:
            return jsonify(error="unknown short code"), 404

        if not _safe_target(target):
            abort(400, description="unsafe redirect target")

        # 301: permanent redirect (cacheable by browsers and search engines)
        return redirect(target, code=301)

    return app


app = create_app()
