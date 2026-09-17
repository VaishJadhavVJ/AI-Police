from flask import Flask, jsonify, redirect


SHORT_URLS = {
    "abc123": "https://example.com/articles/intro",
}


def create_app():
    app = Flask(__name__)

    @app.get("/r/<code>")
    def resolve(code):
        target = SHORT_URLS.get(code)
        if target is None:
            return jsonify(error="unknown short code"), 404
        return redirect(target, code=302)

    return app


app = create_app()
