import time

from flask import Flask, jsonify


class RateLimiter:
    def __init__(self, max_requests, window_seconds, clock=time.monotonic):
        self.max_requests = max_requests
        self.window_seconds = window_seconds
        self.clock = clock
        self._requests = []

    def allow(self):
        now = self.clock()
        # Keep only timestamps still inside the sliding window.
        self._requests = [t for t in self._requests if now - t < self.window_seconds]
        if len(self._requests) >= self.max_requests:
            return False
        self._requests.append(now)
        return True


def create_app(clock=time.monotonic):
    app = Flask(__name__)
    limiter = RateLimiter(max_requests=2, window_seconds=60, clock=clock)

    @app.post("/check")
    def check():
        return jsonify(allowed=limiter.allow())

    return app


app = create_app()
