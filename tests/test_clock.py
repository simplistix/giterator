from datetime import timedelta, timezone

from testfixtures import compare

from giterator.clock import Clock


class TestClock:
    def test_now_returns_utc_datetimes(self) -> None:
        clock = Clock()
        compare(clock.now().tzinfo, expected=timezone.utc)

    def test_now_increases_monotonically_but_not_uniformly(self) -> None:
        clock = Clock()
        first, second, third = clock.now(), clock.now(), clock.now()
        compare(second - first, expected=timedelta(seconds=10))
        compare(third - second, expected=timedelta(seconds=20))
