import threading
import time

from flask import Flask, jsonify


class RateLimiter:
    """Sliding-window rate limiter.

    Safe to share across threads: the purge/count/append sequence in
    ``allow`` is atomic, so concurrent callers can never exceed
    ``max_requests`` within the window.
    """

    def __init__(self, max_requests, window_seconds, clock=time.monotonic):
        if max_requests < 1:
            raise ValueError("max_requests must be at least 1")
        if window_seconds <= 0:
            raise ValueError("window_seconds must be positive")
        self.max_requests = max_requests
        self.window_seconds = window_seconds
        self.clock = clock
        self._requests = []
        # Guard the check-then-act sequence below; without it, two threads
        # can both observe a free slot and both append, exceeding the limit.
        self._lock = threading.Lock()

    def allow(self):
        now = self.clock()
        with self._lock:
            self._requests = [
                timestamp
                for timestamp in self._requests
                if now - timestamp < self.window_seconds
            ]
            if len(self._requests) >= self.max_requests:
                return False
            self._requests.append(now)
            return True


def create_app():
    app = Flask(__name__)
    limiter = RateLimiter(max_requests=2, window_seconds=60)

    @app.post("/check")
    def check():
        return jsonify(allowed=limiter.allow())

    return app


app = create_app()
