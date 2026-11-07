"""Deterministic crash injection for the recovery test (scripts/crash_test.py)."""
import os
from pathlib import Path

_points = {p for p in os.environ.get("CRASH_POINTS", "").split(",") if p}
_marker = Path(os.environ.get("CRASH_MARKER", "state/.crash_fired"))


def crashpoint(name: str) -> None:
    if name not in _points:
        return
    fired = set(_marker.read_text().split()) if _marker.exists() else set()
    if name in fired:
        return
    _marker.parent.mkdir(parents=True, exist_ok=True)
    _marker.write_text(" ".join(sorted(fired | {name})))
    print(f"[fault-injection] hard exit at {name}", flush=True)
    os._exit(137)
