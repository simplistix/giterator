from datetime import datetime, timedelta, timezone


class Clock:
    """
    Return a sequence of datetimes in UTC that increase monotonically but
    not uniformly.
    """

    def __init__(self):
        self._now = datetime(2001, 1, 1, 0).astimezone(timezone.utc)
        self._current_delta = 10

    def now(self) -> datetime:
        now = self._now
        self._now = now + timedelta(seconds=self._current_delta)
        self._current_delta += 10
