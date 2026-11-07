"""Deterministic crash injection for the recovery test (scripts/crash_test.py). Off unless CRASH_POINTS is set.

CRASH_POINTS=after_approval_post,after_apply_post,after_auto_put,mid_chunk  -> the process hard-exits (no
cleanup, like kill -9) the first time it reaches each named point. A marker file records which points have
fired so the restarted process doesn't crash at the same point again.
"""
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
