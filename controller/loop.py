"""The always-on loop: ingest -> reconcile -> detect -> decide -> advance. Safe to kill and restart anywhere."""
from __future__ import annotations

import json
import logging
import os
import resource
import time

from . import settings as S
from .api import SimAPI
from .cohorts import Registry
from .data import Evidence
from .governance import Governance
from .ingest import Ingestor
from .planner import Planner
from .policies import callerid, prompts, schedule
from .simtime import label, minute_of
from .store import Store

log = logging.getLogger("controller")


class Ctx:
    """Everything a policy needs, passed explicitly."""

    def __init__(self, api: SimAPI, store: Store):
        self.api, self.store = api, store
        self.now = 0
        self.started_minute = None
        self.wfs: dict[str, dict] = {}
        self.registry = Registry(store)
        self._live: dict[str, dict] = {}
        self._credits = None

    # ---- config
    def refresh_config(self, wf: str) -> dict:
        c = self.api.config(wf)
        self._live[wf] = c
        self.store.x("INSERT OR IGNORE INTO configs VALUES (?,?,?,?,?)",
                     (wf, c["version"], c["actor"], c["applied_at"], json.dumps(c["config"])))
        return c

    def live(self, wf: str) -> dict:
        return self._live.get(wf) or self.refresh_config(wf)

    # ---- misc
    def credits(self) -> float:
        return float(self.api.state()["credits_remaining"])

    def incident_open(self, wf: str) -> bool:
        return prompts.open_incident(self, wf)[0] is not None

    def prompt_since(self, wf: str) -> int:
        rows = self.store.q("SELECT minute, body FROM world_events WHERE workflow_id=? AND type='config_changed' "
                            "ORDER BY event_id DESC LIMIT 50", (wf,))
        for m, body in rows:
            if "prompt_version" in json.loads(body).get("changed_dims", []):
                return m
        return -10 ** 9


def _single_instance(db: str):
    """Two controllers on one state DB would both drive the world: refuse the second one."""
    import fcntl
    os.makedirs(os.path.dirname(os.path.abspath(db)), exist_ok=True)
    fh = open(db + ".lock", "w")
    try:
        fcntl.flock(fh, fcntl.LOCK_EX | fcntl.LOCK_NB)
    except OSError:
        raise SystemExit(f"another controller is already running on {db}")
    fh.write(str(os.getpid()))
    fh.flush()
    return fh


class Controller:
    def __init__(self, url: str, db: str, store_calls: bool = True):
        self._lock = _single_instance(db)
        self.api = SimAPI(url)
        self.store = Store(db)
        self.ctx = Ctx(self.api, self.store)
        self.ingestor = Ingestor(self.api, self.store, store_calls=store_calls)
        self.ctx.codes = self.ingestor.codes
        self.ctx.ev = Evidence(self.store, self.ingestor.codes)
        self.gov = Governance(self.ctx)
        self.planner = Planner(self.ctx, self.gov)
        self.dirty: set[str] = set()

    # ------------------------------------------------------------------ world events (inside the ingest txn)
    def on_world_event(self, ev: dict) -> None:
        if ev["type"] != "config_changed":
            return
        wf = ev["workflow_id"]
        self.dirty.add(wf)
        if ev.get("actor") == "supervisor":
            m = minute_of(ev["ts"])
            for d in ev.get("changed_dims", []):
                self.store.x("INSERT INTO frozen_dims VALUES (?,?,?,1,?) ON CONFLICT DO UPDATE SET "
                             "until_minute=excluded.until_minute, sticky=1, reason=excluded.reason",
                             (wf, d, m + S.SUPERVISOR_FREEZE_MIN, f"supervisor edit v{ev['version']} at {label(m)}"))
            self.store.decide(m, wf, "supervisor.edit",
                              f"supervisor changed {', '.join(ev.get('changed_dims', []))} (v{ev['version']}); "
                              f"controller leaves these as set for 24h and will only touch them again through an "
                              f"approval request", ev)

    # ------------------------------------------------------------------ start-up
    def _check_same_world(self, st: dict) -> None:
        """Refuse to resume on a DB that belongs to a different simulator run (README: a simulator restart is a new..."""
        hist = self.api.list_chunks("history", -1)
        fp = {"scenario": st["scenario"], "first_chunk": [hist[0]["first_event_id"], hist[0]["last_event_id"],
                                                          hist[0]["until_minute"]] if hist else None}
        old = self.store.get_meta("world")
        if old is None:
            self.store.set_meta("world", fp)
            return
        done = self.store.q1("SELECT MAX(last_event_id) FROM chunks_done") or 0
        if old != fp or st["last_event_id"] < done:
            raise SystemExit(f"state DB {self.store.path} belongs to another simulator run ({old}); this simulator "
                             f"is {fp} at event {st['last_event_id']} (we have {done}). Use a new CONTROLLER_DB.")

    def bootstrap(self) -> None:
        st = self.api.state()
        self._check_same_world(st)
        self.ctx.now = st["sim_minute"]
        for w in self.api.workflows():
            self.ctx.wfs[w["workflow_id"]] = w
            self.store.x("INSERT OR REPLACE INTO workflows VALUES (?,?,?)",
                         (w["workflow_id"], w["tenant_id"], json.dumps(w)))
        first_run = not self.store.get_meta("bootstrapped")
        self.ctx.started_minute = self.store.get_meta("started_minute", st["sim_minute"])
        self.store.set_meta("started_minute", self.ctx.started_minute)
        t0 = time.time()
        ing = self.ingestor.run(self.on_world_event)
        log.info("ingested %d events from %d chunks in %.1fs", ing["events"], ing["chunks"], ing["wall_s"])
        for wf in self.ctx.wfs:
            self.ctx.refresh_config(wf)
        if first_run:
            with self.store.txn():
                for wf in self.ctx.wfs:
                    # business default config = experiment control
                    self.store.set_meta(f"default_cfg:{wf}", self.ctx.live(wf)["config"])
                    cells = schedule.discover_cells(self.ctx, wf)
                    for c in cells:
                        self.ctx.registry.add(wf, "schedule", c["where"], self.ctx.now,
                                              f"call-time cell learned from history ({int(c['dials'])} dials)")
                    self.store.decide(self.ctx.now, wf, "bootstrap.cohorts",
                                      f"{len(cells)} call-time cohorts from history: "
                                      + ", ".join(_fmt_where(c["where"]) for c in cells), cells)
                    callerid.bootstrap(self.ctx, wf)
                    prompts.baseline(self.ctx, wf)
                self.store.set_meta("bootstrapped", True)
                self.store.decide(self.ctx.now, None, "bootstrap.done",
                                  f"bootstrapped {len(self.ctx.wfs)} workflows from history in "
                                  f"{time.time() - t0:.1f}s", {"events": ing["events"]})
        else:
            self.store.decide(self.ctx.now, None, "recovery.restart",
                              f"controller restarted at {label(self.ctx.now)}; resuming from chunk "
                              f"{self.ingestor.last_chunk()}", None)
        self.gov.reconcile()

    # ------------------------------------------------------------------ main loop
    def run(self, max_steps: int | None = None) -> None:
        self.api.wait_ready()
        self.bootstrap()
        steps = 0
        while True:
            t0 = time.time()
            st = self.api.state()
            self.ctx.now = st["sim_minute"]
            ing = self.ingestor.run(self.on_world_event)
            t_ing = time.time() - t0
            for wf in self.ctx.wfs:
                self.ctx.refresh_config(wf)
            self.gov.poll()
            for wf in self.ctx.wfs:
                try:
                    self.planner.step(wf)
                except Exception:   # one workflow's bug must not stop the others
                    log.exception("planner failed for %s at %s", wf, label(self.ctx.now))
                    self.store.alert(self.ctx.now, "page", wf, f"{wf}: planner error",
                                     "see controller log; other workflows continue")
            self._metrics(st, ing, t_ing, time.time() - t0)
            if st["finished"]:
                self.store.decide(self.ctx.now, None, "run.finished", f"scenario finished at {label(self.ctx.now)}",
                                  {"credits_remaining": st["credits_remaining"]})
                log.info("scenario finished")
                return
            r = self.api.advance(S.STEP_MINUTES)
            if r.status == 409:
                continue
            if not r.ok:
                log.warning("advance failed: %s", r)
                time.sleep(2)
            steps += 1
            if self.ctx.now % 1440 == 0:
                log.info("%s  events=%d  credits=%.0f", label(self.ctx.now), self.ingestor.total_events,
                         st["credits_remaining"])
            if max_steps and steps >= max_steps:
                return

    def _metrics(self, st, ing, t_ing, t_step) -> None:
        m = self.ctx.now
        s = self.store
        with s.txn():
            s.metric(m, "ingest_events", ing["events"])
            s.metric(m, "ingest_wall_s", t_ing)
            s.metric(m, "ingest_events_per_s", ing["events"] / t_ing if t_ing > 0 else 0)
            s.metric(m, "decision_lag_s", t_step)
            s.metric(m, "credits_remaining", st["credits_remaining"])
            s.metric(m, "rss_mb", resource.getrusage(resource.RUSAGE_SELF).ru_maxrss / 1024)
            s.metric(m, "pending_approvals", s.q1("SELECT COUNT(*) FROM proposals WHERE status IN "
                                                   "('pending','approved','applying')"))
            s.metric(m, "decisions_last_hour", s.q1("SELECT COUNT(*) FROM decisions WHERE minute > ?", (m - 60,)))
            total = float(s.get_meta("credits_total", st["credits_remaining"]))
            s.set_meta("credits_total", max(total, st["credits_remaining"]))
            if st["credits_remaining"] < S.ALERT_CREDIT_FRACTION * total:
                s.alert(m, "page" if any(self.ctx.incident_open(w) for w in self.ctx.wfs) else "ticket", None,
                        f"credits low: {st['credits_remaining']:.0f} of {total:.0f}",
                        "routine spend stops at the reserve; incidents can still validate")
            lapsed = s.q1("SELECT COUNT(*) FROM proposals WHERE status='lapsed' AND submitted_minute > ?", (m - 1440,))
            if lapsed:
                s.alert(m, "page", None, f"{lapsed} approved change(s) lapsed in 24h",
                        "the loop is not polling often enough or is stuck; check decision_lag_s")


def _fmt_where(w: dict) -> str:
    return " & ".join(f"{k}={'|'.join(v)}" for k, v in w.items())


def main_run(url: str, db: str, verbose: bool = False) -> None:
    logging.basicConfig(level=logging.DEBUG if verbose else logging.INFO,
                        format="%(asctime)s %(levelname)s %(name)s: %(message)s")
    logging.getLogger("httpx").setLevel(logging.WARNING)
    Controller(url, db, store_calls=os.environ.get("STORE_CALLS", "1") == "1").run()
