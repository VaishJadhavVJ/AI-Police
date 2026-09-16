from flask import Flask, jsonify, request


def fahrenheit_to_celsius(fahrenheit):
    return (fahrenheit - 32) * 5 / 9


def kilometers_to_miles(kilometers):
    return kilometers * 0.621371


def create_app():
    app = Flask(__name__)

    @app.post("/convert")
    def convert():
        body = request.get_json()
        value = float(body["value"])
        conversion = body["conversion"]
        if conversion == "f_to_c":
            result = fahrenheit_to_celsius(value)
        elif conversion == "km_to_miles":
            result = kilometers_to_miles(value)
        else:
            return jsonify(error="unknown conversion"), 400
        return jsonify(result=round(result, 6))

    return app


app = create_app()