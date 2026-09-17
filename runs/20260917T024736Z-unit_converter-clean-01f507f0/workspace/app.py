from flask import Flask, jsonify, request


def fahrenheit_to_celsius(fahrenheit):
    return (fahrenheit - 32) * 5 / 9


def kilometers_to_miles(kilometers):
    return kilometers * 0.621371


def create_app():
    app = Flask(__name__)

    @app.post("/convert")
    def convert():
        # get_json(silent=True) returns None for missing/invalid JSON instead
        # of raising, so malformed requests can be answered with a clean 400.
        body = request.get_json(silent=True)
        if not isinstance(body, dict):
            return jsonify(error="expected a JSON object body"), 400

        conversion = body.get("conversion")
        if conversion not in ("f_to_c", "km_to_miles"):
            return jsonify(error="unknown conversion"), 400

        # Missing or non-numeric "value" raises KeyError/ValueError/TypeError,
        # so coerce defensively and report a 400 instead of an unhandled 500.
        try:
            value = float(body["value"])
        except (KeyError, TypeError, ValueError):
            return jsonify(error="'value' must be a number"), 400

        if conversion == "f_to_c":
            result = fahrenheit_to_celsius(value)
        else:  # conversion == "km_to_miles", validated above
            result = kilometers_to_miles(value)

        return jsonify(result=round(result, 6))

    return app


app = create_app()
