"""Thin HTTP client for the simulator. The only way the controller learns anything about the world.

Retry policy:
- GETs are retried on connection errors and 5xx with backoff.
- POSTs that carry our own idempotency key (approvals, auto-apply) are retried too: a retry that lands twice
  comes back as 409 duplicate_proposal_id, which the governance client reconciles.
- /sim/advance is NOT blindly retried: on a timeout we read /sim/state to see whether time moved.
- /llm and /validation spend credits, so they are never retried automatically.
"""
from __future__ import annotations

import logging
import time

import httpx

log = logging.getLogger("controller.api")


class ApiResult:
    __slots__ = ("status", "body")

    def __init__(self, status: int, body):
        self.status, self.body = status, body

    @property
    def ok(self) -> bool:
        return 200 <= self.status < 300

    @property
    def error(self) -> str | None:
        return self.body.get("error") if isinstance(self.body, dict) else None

    def __repr__(self):
        return f"ApiResult({self.status}, {str(self.body)[:200]})"


class SimAPI:
    def __init__(self, base_url: str, timeout: float = 300.0):
        self.base_url = base_url.rstrip("/")
        self.c = httpx.Client(base_url=self.base_url, timeout=timeout)
        self.calls = 0

    # ------------------------------------------------------------------ plumbing
    def _send(self, method: str, path: str, retry: bool, **kw) -> ApiResult:
        delay = 0.5
        for attempt in range(8 if retry else 1):
            try:
                self.calls += 1
                r = self.c.request(method, path, **kw)
                if r.status_code >= 500 and retry and attempt < 7:
                    log.warning("%s %s -> %s, retrying", method, path, r.status_code)
                else:
                    try:
                        body = r.json()
                    except ValueError:
                        body = r.text
                    return ApiResult(r.status_code, body)
            except httpx.TransportError as e:
                if not retry or attempt == 7:
                    raise
                log.warning("%s %s transport error %s, retrying", method, path, e)
            time.sleep(delay)
            delay = min(delay * 2, 10)
        raise RuntimeError("unreachable")

    def _get(self, path, **params) -> ApiResult:
        return self._send("GET", path, True, params=params or None)

    def wait_ready(self, seconds: float | None = None) -> None:
        """Wait for the simulator to come up (it may start after us). CONTROLLER_WAIT_S overrides (default 600)."""
        import os
        seconds = float(os.environ.get("CONTROLLER_WAIT_S", 600)) if seconds is None else seconds
        end = time.time() + seconds
        while True:
            try:
                if self.c.get("/health").status_code == 200:
                    return
            except httpx.TransportError:
                pass
            if time.time() > end:
                raise SystemExit(f"simulator at {self.base_url} not reachable")
            time.sleep(1)

    # ------------------------------------------------------------------ reads
    def state(self) -> dict:
        return self._get("/sim/state").body

    def workflows(self) -> list[dict]:
        return self._get("/workflows").body

    def config(self, wid: str) -> dict:
        return self._get(f"/workflows/{wid}/config").body

    def config_history(self, wid: str) -> list[dict]:
        return self._get(f"/workflows/{wid}/config/history").body

    def list_chunks(self, kind: str, after: int) -> list[dict]:
        return self._get("/events/chunks", kind=kind, after=after).body

    def chunk_text(self, n: int) -> str:
        delay = 0.5
        for attempt in range(8):
            try:
                r = self.c.get(f"/events/chunks/{n}")
                if r.status_code == 200:
                    return r.text
                if r.status_code < 500:
                    raise RuntimeError(f"chunk {n}: HTTP {r.status_code}")
            except httpx.TransportError:
                if attempt == 7:
                    raise
            time.sleep(delay)
            delay = min(delay * 2, 10)
        raise RuntimeError(f"chunk {n} unavailable")

    def list_approvals(self, wid: str | None = None, status: str | None = None) -> list[dict]:
        p = {k: v for k, v in (("workflow_id", wid), ("status", status)) if v}
        return self._get("/approvals", **p).body

    def get_approval(self, aid: str) -> ApiResult:
        return self._get(f"/approvals/{aid}")

    # ------------------------------------------------------------------ writes
    def advance(self, minutes: int) -> ApiResult:
        before = self.state()["sim_minute"]
        try:
            return self._send("POST", "/sim/advance", False, json={"minutes": minutes})
        except httpx.TransportError:
            # Did time move? If it did, the advance happened and events are in chunks; don't advance twice.
            for _ in range(30):
                try:
                    st = self.state()
                    break
                except httpx.TransportError:
                    time.sleep(2)
            else:
                raise
            if st["sim_minute"] != before:
                return ApiResult(200, {**st, "new_chunks": [], "recovered": True})
            return self._send("POST", "/sim/advance", False, json={"minutes": minutes})

    def request_approval(self, body: dict) -> ApiResult:
        return self._send("POST", "/approvals", True, json=body)

    def apply(self, wid: str, aid: str) -> ApiResult:
        return self._send("POST", f"/workflows/{wid}/apply", True, json={"approval_id": aid})

    def auto_apply(self, wid: str, body: dict) -> ApiResult:
        return self._send("PUT", f"/workflows/{wid}/config", True, json=body)

    def suggest_fixes(self, wid: str, problem: str) -> ApiResult:
        return self._send("POST", "/llm/suggest-fixes", False, json={"workflow_id": wid, "problem": problem})

    def validate(self, wid: str, prompt_version: str, n: int) -> ApiResult:
        return self._send("POST", "/validation/runs", False,
                          json={"workflow_id": wid, "prompt_version": prompt_version, "n": n})
