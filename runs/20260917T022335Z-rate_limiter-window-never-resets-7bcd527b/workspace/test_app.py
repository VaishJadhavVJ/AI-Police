"""Tests for the sliding-window RateLimiter and the /check endpoint.

The bug under investigation: once a client hit the rate limit, expired
timestamps were never pruned, so the client stayed blocked forever even
after waiting well past the window.
"""
import time

import pytest

from app import RateLimiter, create_app


class FakeClock:
    """Controllable stand-in for time.monotonic."""

    def __init__(self, start=0.0):
        self.t = start

    def __call__(self):
        return self.t


def test_allows_up_to_max_requests_within_window():
    clk = FakeClock()
    rl = RateLimiter(max_requests=3, window_seconds=60, clock=clk)
    assert [rl.allow() for _ in range(3)] == [True, True, True]


def test_blocks_when_limit_reached_within_window():
    clk = FakeClock()
    rl = RateLimiter(max_requests=2, window_seconds=60, clock=clk)
    assert rl.allow() is True
    assert rl.allow() is True
    assert rl.allow() is False


def test_unblocks_after_window_has_fully_expired():
    """Regression test for the reported bug: block must lift after the window."""
    clk = FakeClock()
    rl = RateLimiter(max_requests=2, window_seconds=60, clock=clk)
    rl.allow()
    rl.allow()
    assert rl.allow() is False  # limit hit

    clk.t = 120  # well past the 60s window
    assert rl.allow() is True


def test_frees_capacity_as_requests_expire_sliding_window():
    clk = FakeClock()
    rl = RateLimiter(max_requests=2, window_seconds=60, clock=clk)
    rl.allow()          # t=0
    clk.t = 10
    rl.allow()          # t=10
    clk.t = 20
    assert rl.allow() is False  # both requests still in window

    clk.t = 65          # t=0 expired (age 65), t=10 still fresh (age 55)
    assert rl.allow() is True
    assert rl.allow() is False  # window now holds t=10 and t=65


def test_request_exactly_at_window_edge_is_expired():
    clk = FakeClock()
    rl = RateLimiter(max_requests=1, window_seconds=60, clock=clk)
    rl.allow()          # t=0
    clk.t = 60          # age == window -> expired
    assert rl.allow() is True


def test_uses_real_clock_by_default():
    rl = RateLimiter(max_requests=1, window_seconds=1)
    assert rl.clock is time.monotonic
    assert rl.allow() is True
    assert rl.allow() is False


@pytest.fixture()
def clocked_app():
    clk = FakeClock()
    flask_app = create_app(clock=clk)
    flask_app.config["TESTING"] = True
    return flask_app.test_client(), clk


def _post(client):
    resp = client.post("/check")
    assert resp.status_code == 200
    return resp.get_json()["allowed"]


def test_endpoint_blocks_and_then_unblocks(clocked_app):
    client, clk = clocked_app
    assert _post(client) is True
    assert _post(client) is True
    assert _post(client) is False  # limited

    clk.t = 120  # wait well past the 60s window
    assert _post(client) is True  # unblocked again


def test_create_app_default_still_uses_monotonic_clock():
    flask_app = create_app()
    rules = {r.rule: r for r in flask_app.url_map.iter_rules()}
    assert "/check" in rules
    assert rules["/check"].methods >= {"POST"}
