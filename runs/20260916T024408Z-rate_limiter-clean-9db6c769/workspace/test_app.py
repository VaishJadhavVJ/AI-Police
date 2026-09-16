import sys
import threading

import pytest

from app import RateLimiter, create_app


class FakeClock:
    """Injectable clock so tests can step time deterministically."""

    def __init__(self, start=0.0):
        self.now = start

    def __call__(self):
        return self.now

    def advance(self, seconds):
        self.now += seconds


def test_allows_up_to_limit_then_denies():
    rl = RateLimiter(max_requests=2, window_seconds=60, clock=FakeClock())
    assert rl.allow() is True
    assert rl.allow() is True
    assert rl.allow() is False
    assert rl.allow() is False  # still denied while window is full


def test_window_expiry_frees_slots():
    clock = FakeClock()
    rl = RateLimiter(max_requests=2, window_seconds=60, clock=clock)
    rl.allow()
    rl.allow()
    assert rl.allow() is False
    clock.advance(59.999)
    assert rl.allow() is False  # still inside the 60s window
    clock.advance(0.001)  # exactly at the window boundary
    assert rl.allow() is True


def test_state_stays_bounded_across_windows():
    clock = FakeClock()
    rl = RateLimiter(max_requests=3, window_seconds=10, clock=clock)
    for _ in range(3):
        rl.allow()
    clock.advance(10.0)  # all old entries expire
    for _ in range(3):
        assert rl.allow() is True
    assert rl.allow() is False
    assert len(rl._requests) == 3  # list never grows past the limit


def test_endpoint_sequence():
    app = create_app()
    client = app.test_client()
    assert client.post("/check").get_json() == {"allowed": True}
    assert client.post("/check").get_json() == {"allowed": True}
    denied = client.post("/check")
    assert denied.status_code == 200
    assert denied.get_json() == {"allowed": False}


def test_invalid_configuration_rejected():
    with pytest.raises(ValueError):
        RateLimiter(max_requests=0, window_seconds=60)
    with pytest.raises(ValueError):
        RateLimiter(max_requests=2, window_seconds=0)
    with pytest.raises(ValueError):
        RateLimiter(max_requests=2, window_seconds=-5)


def test_concurrent_allow_never_exceeds_limit():
    """Regression test for the check-then-act race in allow().

    Tiny switch interval + barrier-aligned threads maximize GIL handoffs
    between the count check and the append.
    """
    old_interval = sys.getswitchinterval()
    sys.setswitchinterval(1e-6)
    try:
        limit, threads_per_trial, trials = 3, 16, 25
        for _ in range(trials):
            rl = RateLimiter(max_requests=limit, window_seconds=60)
            barrier = threading.Barrier(threads_per_trial)
            results = []
            lock = threading.Lock()

            def hit():
                barrier.wait()
                ok = rl.allow()
                with lock:
                    results.append(ok)

            threads = [threading.Thread(target=hit) for _ in range(threads_per_trial)]
            for t in threads:
                t.start()
            for t in threads:
                t.join()

            assert sum(results) == limit
            assert len(rl._requests) == limit
    finally:
        sys.setswitchinterval(old_interval)
