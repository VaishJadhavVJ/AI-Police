import sys
import threading

import pytest

from app import RateLimiter, create_app


class FakeClock:
    """Deterministic clock so time-based behavior can be tested exactly."""

    def __init__(self, start=0.0):
        self.now = start

    def __call__(self):
        return self.now

    def advance(self, seconds):
        self.now += seconds


@pytest.fixture
def clock():
    return FakeClock()


class TestRateLimiter:
    def test_allows_up_to_max_requests(self, clock):
        limiter = RateLimiter(max_requests=2, window_seconds=60, clock=clock)
        assert limiter.allow() is True
        assert limiter.allow() is True
        assert limiter.allow() is False

    def test_blocks_until_window_elapses(self, clock):
        limiter = RateLimiter(max_requests=2, window_seconds=60, clock=clock)
        limiter.allow()
        limiter.allow()
        assert limiter.allow() is False
        clock.advance(59.9)
        assert limiter.allow() is False  # still inside the 60s window
        clock.advance(0.1)  # t=60: the original requests have aged out
        assert limiter.allow() is True

    def test_requests_expire_independently(self, clock):
        limiter = RateLimiter(max_requests=2, window_seconds=60, clock=clock)
        assert limiter.allow() is True  # t=0
        clock.advance(50)
        assert limiter.allow() is True  # t=50
        assert limiter.allow() is False  # t=50: two requests in window
        clock.advance(10)  # t=60: only the t=0 request has expired
        assert limiter.allow() is True

    def test_denied_requests_are_not_recorded(self, clock):
        limiter = RateLimiter(max_requests=2, window_seconds=60, clock=clock)
        limiter.allow()
        limiter.allow()
        assert limiter.allow() is False
        clock.advance(61)
        # Both real requests expired; a denied request must not count as one.
        assert limiter.allow() is True
        assert limiter.allow() is True
        assert limiter.allow() is False

    def test_uses_monotonic_clock_by_default(self):
        limiter = RateLimiter(max_requests=1, window_seconds=60)
        assert limiter.allow() is True
        assert limiter.allow() is False


class TestThreadSafety:
    def test_concurrent_callers_cannot_exceed_limit(self):
        limiter = RateLimiter(max_requests=5, window_seconds=60)
        n_threads = 60
        results = []
        barrier = threading.Barrier(n_threads)

        old_interval = sys.getswitchinterval()
        # Force frequent GIL hand-offs so the check-then-act window in
        # allow() is exercised from many interleavings.
        sys.setswitchinterval(1e-6)
        try:

            def worker():
                barrier.wait()
                results.append(limiter.allow())

            threads = [threading.Thread(target=worker) for _ in range(n_threads)]
            for t in threads:
                t.start()
            for t in threads:
                t.join()
        finally:
            sys.setswitchinterval(old_interval)

        assert sum(results) == 5


class TestFlaskApp:
    @pytest.fixture
    def client(self):
        return create_app().test_client()

    def test_allows_then_blocks_within_window(self, client):
        assert client.post("/check").get_json() == {"allowed": True}
        assert client.post("/check").get_json() == {"allowed": True}
        assert client.post("/check").get_json() == {"allowed": False}

    def test_check_is_post_only(self, client):
        assert client.get("/check").status_code == 405

    def test_unknown_route_returns_404(self, client):
        assert client.post("/nope").status_code == 404

    def test_each_app_has_an_independent_limiter(self):
        c1 = create_app().test_client()
        c2 = create_app().test_client()
        assert c1.post("/check").get_json() == {"allowed": True}
        assert c2.post("/check").get_json() == {"allowed": True}
