import pytest

from app import RateLimiter, create_app


class FakeClock:
    def __init__(self):
        self.t = 0.0

    def __call__(self):
        return self.t

    def advance(self, seconds):
        self.t += seconds


@pytest.fixture
def clock():
    return FakeClock()


def test_allows_exactly_max_requests_then_rejects(clock):
    limiter = RateLimiter(max_requests=2, window_seconds=60, clock=clock)
    assert limiter.allow() is True
    assert limiter.allow() is True
    assert limiter.allow() is False, "3rd request must be rejected, not allowed"


def test_max_requests_one(clock):
    limiter = RateLimiter(max_requests=1, window_seconds=60, clock=clock)
    assert limiter.allow() is True
    assert limiter.allow() is False


def test_capacity_restored_after_window(clock):
    limiter = RateLimiter(max_requests=2, window_seconds=60, clock=clock)
    assert [limiter.allow() for _ in range(3)] == [True, True, False]
    clock.advance(60.1)  # window has fully elapsed
    assert limiter.allow() is True
    assert limiter.allow() is True
    assert limiter.allow() is False


def test_window_is_sliding(clock):
    limiter = RateLimiter(max_requests=2, window_seconds=60, clock=clock)
    assert limiter.allow() is True
    clock.advance(30)
    assert limiter.allow() is True
    clock.advance(30.1)  # first timestamp just expired, second is 30.1s old
    assert limiter.allow() is True
    assert limiter.allow() is False  # still limited by the 30.1s-old request


def test_endpoint_enforces_limit(client):
    results = [client.post("/check").get_json()["allowed"] for _ in range(3)]
    assert results == [True, True, False]


@pytest.fixture
def client():
    app = create_app()
    app.config["TESTING"] = True
    with app.test_client() as client:
        yield client
