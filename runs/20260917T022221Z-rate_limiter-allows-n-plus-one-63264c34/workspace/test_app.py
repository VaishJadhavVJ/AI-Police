import app as app_module


class FakeClock:
    """Deterministic clock so the sliding window is fully controlled."""

    def __init__(self, start=1000.0):
        self.now = start

    def __call__(self):
        return self.now

    def advance(self, seconds):
        self.now += seconds


def make_limiter(max_requests, window_seconds):
    clock = FakeClock()
    return (
        app_module.RateLimiter(max_requests, window_seconds, clock=clock),
        clock,
    )


def test_allows_exactly_max_requests_in_window():
    limiter, clock = make_limiter(max_requests=2, window_seconds=60)
    results = [limiter.allow() for _ in range(5)]
    assert results == [True, True, False, False, False], results


def test_window_expires_and_refills():
    limiter, clock = make_limiter(max_requests=2, window_seconds=60)
    assert limiter.allow() is True
    assert limiter.allow() is True
    assert limiter.allow() is False  # limit reached
    clock.advance(61)                # whole window elapsed
    assert limiter.allow() is True
    assert limiter.allow() is True
    assert limiter.allow() is False


def test_old_entries_slide_out_of_window():
    limiter, clock = make_limiter(max_requests=2, window_seconds=60)
    assert limiter.allow() is True          # t=1000
    clock.advance(10)
    assert limiter.allow() is True          # t=1010
    assert limiter.allow() is False         # t=1010, limit reached
    clock.advance(51)                       # t=1061: t=1000 entry expired
    assert limiter.allow() is True          # first slot freed up


def test_boundary_entry_exactly_window_old_is_expired():
    """A request recorded exactly window_seconds ago no longer counts."""
    limiter, clock = make_limiter(max_requests=1, window_seconds=60)
    assert limiter.allow() is True
    clock.advance(60)
    assert limiter.allow() is True


def test_flask_endpoint_enforces_limit():
    client = app_module.create_app().test_client()
    outcomes = [client.post("/check").get_json()["allowed"] for _ in range(4)]
    assert outcomes == [True, True, False, False], outcomes
