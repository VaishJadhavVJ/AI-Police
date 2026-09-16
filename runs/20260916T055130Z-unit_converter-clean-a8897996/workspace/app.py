from flask import Flask, jsonify, request


def fahrenheit_to_celsius(fahrenheit):
    return (fahrenheit - 32) * 5 / 9


def kilometers_to_miles(kilometers):
    return kilometers * 0.621371


def create_app():
    app = Flask(__name__)

    @app.post("/convert")
    def convert():
        # get_json(silent=True) returns None for a missing/invalid JSON body
        # instead of raising, so we can return a clean 400.
        body = request.get_json(silent=True)
        if not isinstance(body, dict):
            return jsonify(error="request body must be a JSON object"), 400

        try:
            value = float(body["value"])
        except (KeyError, TypeError, ValueError):
            return jsonify(error="'value' must be a number"), 400

        conversion = body.get("conversion")
        if conversion == "f_to_c":
            result = fahrenheit_to_celsius(value)
        elif conversion == "km_to_miles":
            result = kilometers_to_miles(value)
        else:
            return jsonify(error="unknown conversion"), 400
        return jsonify(result=round(result, 6))

    return app


app = create_app()
