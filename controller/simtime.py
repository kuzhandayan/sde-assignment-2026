"""Sim-time helpers. D0 00:00 = 2027-01-04T00:00+05:30. Minutes before D0 are negative (history)."""
from __future__ import annotations

import datetime as dt

D0 = dt.date(2027, 1, 4)
MIN_PER_DAY = 1440
_day_cache: dict[str, int] = {}


def minute_of(ts: str) -> int:
    """'2027-01-05T09:07:00+05:30' -> sim minute. Fast path: cache the date part."""
    d = ts[:10]
    days = _day_cache.get(d)
    if days is None:
        days = (dt.date.fromisoformat(d) - D0).days
        _day_cache[d] = days
    return days * MIN_PER_DAY + int(ts[11:13]) * 60 + int(ts[14:16])


def day_of(minute: int) -> int:
    return minute // MIN_PER_DAY


def hour_of(minute: int) -> int:
    return (minute % MIN_PER_DAY) // 60


def label(minute: int) -> str:
    """Sim minute -> 'D3 14:00' (the way the README talks about time)."""
    d, m = divmod(minute, MIN_PER_DAY)
    return f"D{d} {m // 60:02d}:{m % 60:02d}"


def parse_label(s: str) -> int:
    """'D3 14:00' or an ISO timestamp -> sim minute."""
    s = s.strip()
    if s[:1] in "Dd":
        day, hm = s.split()
        h, m = hm.split(":")
        return int(day[1:]) * MIN_PER_DAY + int(h) * 60 + int(m)
    return minute_of(s)
