import time

import pytest

from app import RateLimiter, create_app


class FakeClock:
    """Deterministic clock so tests don't need to sleep."""

    def __init__(self, start=0.0):
        self.now = start

    def __call__(self):
        return self.now

    def advance(self, seconds):
        self.now += seconds


def test_blocks_after_max_requests():
    clock = FakeClock()
    rl = RateLimiter(max_requests=2, window_seconds=60, clock=clock)
    assert rl.allow() is True
    assert rl.allow() is True
    assert rl.allow() is False


def test_unblocks_after_window_passes():
    """Regression test: client must be allowed again once the window passes."""
    clock = FakeClock()
    rl = RateLimiter(max_requests=2, window_seconds=60, clock=clock)
    assert rl.allow() is True
    assert rl.allow() is True
    assert rl.allow() is False

    clock.advance(61)  # well past the 60s window
    assert rl.allow() is True
    assert rl.allow() is True
    assert rl.allow() is False  # fresh window is full again


def test_requests_expire_only_after_full_window():
    clock = FakeClock()
    rl = RateLimiter(max_requests=2, window_seconds=60, clock=clock)
    assert rl.allow() is True          # t=0
    clock.advance(30)
    assert rl.allow() is True          # t=30
    clock.advance(31)                  # now=61: t=0 expired, t=30 still counts
    assert rl.allow() is True
    assert rl.allow() is False         # t=30 and t=61 both still in window


def test_unblocks_with_real_clock():
    rl = RateLimiter(max_requests=1, window_seconds=0.05)
    assert rl.allow() is True
    assert rl.allow() is False
    time.sleep(0.06)
    assert rl.allow() is True


def test_http_endpoint_unblocks_after_window():
    clock = FakeClock()
    limiter = RateLimiter(max_requests=2, window_seconds=60, clock=clock)
    client = create_app(limiter=limiter).test_client()

    assert client.post("/check").get_json()["allowed"] is True
    assert client.post("/check").get_json()["allowed"] is True
    assert client.post("/check").get_json()["allowed"] is False

    clock.advance(61)
    assert client.post("/check").get_json()["allowed"] is True
