import sys
import threading
import time

import pytest

from app import RateLimiter, create_app


class FakeClock:
    def __init__(self, start=0.0):
        self.now = start

    def __call__(self):
        return self.now

    def advance(self, seconds):
        self.now += seconds

    def set(self, value):
        self.now = value


# ---------------- RateLimiter unit tests ----------------


def test_allows_up_to_max_then_denies():
    clock = FakeClock()
    limiter = RateLimiter(max_requests=2, window_seconds=60, clock=clock)
    assert limiter.allow() is True
    assert limiter.allow() is True
    assert limiter.allow() is False


def test_denied_requests_are_not_counted():
    clock = FakeClock()
    limiter = RateLimiter(max_requests=1, window_seconds=60, clock=clock)
    assert limiter.allow() is True  # t=0 consumes the only slot
    assert limiter.allow() is False  # denied at t=0, must not be recorded
    clock.set(59)  # still inside the window
    assert limiter.allow() is False
    clock.set(60)  # t=0 has now aged out
    # If the denial had been recorded (at t=0) this would still be False.
    assert limiter.allow() is True


def test_window_boundary_is_exclusive():
    # A request exactly `window_seconds` old no longer counts against the limit.
    clock = FakeClock()
    limiter = RateLimiter(max_requests=1, window_seconds=60, clock=clock)
    assert limiter.allow() is True
    clock.set(59.999)
    assert limiter.allow() is False
    clock.set(60.0)
    assert limiter.allow() is True


def test_sliding_window_keeps_recent_requests():
    clock = FakeClock()
    limiter = RateLimiter(max_requests=2, window_seconds=60, clock=clock)
    assert limiter.allow() is True  # t=0
    clock.set(59)
    assert limiter.allow() is True  # t=59
    clock.set(59.5)
    assert limiter.allow() is False  # both earlier requests still in window
    clock.set(60)
    # t=0 is exactly one window old (pruned); t=59 remains, so one slot is free.
    assert limiter.allow() is True


def test_monotonic_clock_is_the_default():
    limiter = RateLimiter(max_requests=1, window_seconds=60)
    assert limiter.clock is time.monotonic


# ---------------- Flask endpoint tests ----------------


def test_endpoint_allows_then_denies():
    client = create_app().test_client()
    first = client.post("/check")
    second = client.post("/check")
    third = client.post("/check")
    assert first.status_code == 200
    assert first.get_json() == {"allowed": True}
    assert second.get_json() == {"allowed": True}
    assert third.get_json() == {"allowed": False}
    assert third.status_code == 200


def test_app_instances_have_independent_limiters():
    c1 = create_app().test_client()
    c2 = create_app().test_client()
    assert c1.post("/check").get_json() == {"allowed": True}
    assert c1.post("/check").get_json() == {"allowed": True}
    # A separate app instance starts with a fresh budget.
    assert c2.post("/check").get_json() == {"allowed": True}


def test_post_only():
    client = create_app().test_client()
    assert client.get("/check").status_code == 405


# ---------------- Concurrency ----------------


@pytest.fixture
def fast_thread_switching():
    old = sys.getswitchinterval()
    sys.setswitchinterval(1e-6)  # force frequent thread preemption
    yield
    sys.setswitchinterval(old)


def test_concurrent_allow_never_exceeds_limit(fast_thread_switching):
    threads = 50
    rounds = 10
    for _ in range(rounds):
        limiter = RateLimiter(max_requests=5, window_seconds=60)
        barrier = threading.Barrier(threads)
        results = []
        results_lock = threading.Lock()

        def worker():
            barrier.wait()  # all threads hit allow() simultaneously
            allowed = limiter.allow()
            with results_lock:
                results.append(allowed)

        ts = [threading.Thread(target=worker) for _ in range(threads)]
        for t in ts:
            t.start()
        for t in ts:
            t.join()

        # Exactly 5 of the 50 concurrent calls may be admitted.
        assert sum(results) == 5, f"admitted {sum(results)} of {threads} calls"
