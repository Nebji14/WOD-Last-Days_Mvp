"""Limiteur de débit à fenêtre glissante."""

from app.core.rate_limit import RateLimiter


class _Clock:
    def __init__(self) -> None:
        self.now = 0.0

    def __call__(self) -> float:
        return self.now


def test_blocks_above_limit_then_recovers_after_window() -> None:
    clock = _Clock()
    limiter = RateLimiter(clock)

    assert all(limiter.allow("k", limit=3, window_seconds=10) for _ in range(3))
    assert not limiter.allow("k", limit=3, window_seconds=10)

    clock.now = 10.0
    assert limiter.allow("k", limit=3, window_seconds=10)


def test_keys_are_independent() -> None:
    limiter = RateLimiter(_Clock())

    assert limiter.allow("a", limit=1, window_seconds=10)
    assert limiter.allow("b", limit=1, window_seconds=10)
    assert not limiter.allow("a", limit=1, window_seconds=10)
