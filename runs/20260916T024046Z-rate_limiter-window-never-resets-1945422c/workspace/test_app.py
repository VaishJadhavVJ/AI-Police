import pytest

from app import RateLimiter, create_app


class FakeClock:
    """Controllable clock so tests can advance time deterministically."""

    def __init__(self, start=0.0):
        self.now = start

    def __call__(self):
        return self.now

    def advance(self, seconds):
        self.now += seconds


@pytest.fixture
def clock():
    return FakeClock()


def test_allows_requests_under_limit(clock):
    rl = RateLimiter(max_requests=2, window_seconds=60, clock=clock)
    assert rl.allow() is True
    assert rl.allow() is True


def test_blocks_requests_over_limit_within_window(clock):
    rl = RateLimiter(max_requests=2, window_seconds=60, clock=clock)
    rl.allow()
    rl.allow()
    assert rl.allow() is False


def test_allows_again_after_timestamps_age_out_of_window(clock):
    """Regression test for the reported bug: stale timestamps were never
    removed, so the limiter blocked forever after the first burst."""
    rl = RateLimiter(max_requests=2, window_seconds=60, clock=clock)
    rl.allow()
    rl.allow()
    assert rl.allow() is False  # window is full

    clock.advance(61)  # both timestamps are now outside the window
    assert rl.allow() is True
    assert rl.allow() is True
    assert rl.allow() is False  # fresh window is full again


def test_prune_removes_aged_out_timestamps_from_state(clock):
    rl = RateLimiter(max_requests=2, window_seconds=60, clock=clock)
    rl.allow()
    rl.allow()
    clock.advance(61)
    rl.allow()
    assert rl._requests == [61.0], "aged-out timestamps must be dropped, not kept"


def test_timestamp_exactly_at_window_boundary_is_expired(clock):
    rl = RateLimiter(max_requests=2, window_seconds=60, clock=clock)
    rl.allow()
    clock.advance(60)  # timestamp is now exactly window_seconds old
    assert rl.allow() is True


def test_partially_expired_window_frees_only_expired_slots(clock):
    rl = RateLimiter(max_requests=3, window_seconds=60, clock=clock)
    rl.allow()          # t=0: this one will age out
    clock.advance(61)
    rl.allow()          # t=61
    rl.allow()          # t=61
    assert rl.allow() is True   # only 2 in window, limit is 3
    assert rl.allow() is False  # now 3 in window -> blocked


def test_refill_is_continuous_not_all_at_once(clock):
    rl = RateLimiter(max_requests=2, window_seconds=60, clock=clock)
    rl.allow()
    clock.advance(30)
    rl.allow()
    clock.advance(30)  # only the first timestamp has aged out
    assert rl.allow() is True
    assert rl.allow() is False


@pytest.fixture
def client():
    return create_app().test_client()


def test_endpoint_allows_again_after_window(client):
    for _ in range(2):
        resp = client.post("/check")
        assert resp.get_json() == {"allowed": True}
    resp = client.post("/check")
    assert resp.get_json() == {"allowed": False}
