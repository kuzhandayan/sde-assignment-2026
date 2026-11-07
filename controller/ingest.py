"""Event ingestion (C1): chunk-by-chunk, idempotent, restartable.

Each chunk is parsed into aggregate deltas in memory, then written together with `chunks_done(chunk)` in ONE
SQLite transaction. If the process dies mid-chunk, nothing of that chunk is in the store and it is re-read on
restart; if it dies after the commit, the chunk is skipped. Either way every event is counted exactly once.

We never keep raw dials. We keep:
- aggregates (engagement by stratum x features x arm, pickup by hour x features x caller ID, QA by 30-min slot),
- what each customer heard on connected calls (calls_heard), for "why did this customer hear X",
- non-call events verbatim.
"""
from __future__ import annotations

import json
import logging
import time

import numpy as np

from .simtime import minute_of
from .store import Store

log = logging.getLogger("controller.ingest")
FEATS = ("lang", "city_tier", "age_band", "value_band")


class Codes:
    """Lead feature tuple <-> small int. A person's features never change, so a call joins to them by person."""

    def __init__(self, store: Store):
        self.store = store
        self.by_tuple: dict[tuple, int] = {}
        self.by_id: dict[int, tuple] = {}
        for cid, *vals in store.q("SELECT code_id, lang, city_tier, age_band, value_band FROM codes"):
            self.by_tuple[tuple(vals)] = cid
            self.by_id[cid] = tuple(vals)

    def get(self, feats: dict) -> int:
        t = tuple(str(feats[f]) for f in FEATS)
        cid = self.by_tuple.get(t)
        if cid is None:
            cid = len(self.by_tuple) + 1
            self.by_tuple[t] = cid
            self.by_id[cid] = t
            self.store.x("INSERT INTO codes VALUES (?,?,?,?,?)", (cid, *t))
        return cid

    def feats(self, cid: int) -> dict:
        return dict(zip(FEATS, self.by_id[cid]))


class PersonIndex:
    """workflow -> dense array person number -> code id (0 = unknown). Person ids are 'wf:p0001234'."""

    def __init__(self, store: Store):
        self.arr: dict[str, np.ndarray] = {}
        rows = store.q("SELECT workflow_id, pnum, code_id FROM persons")
        for wf, p, c in rows:
            self.set(wf, p, c)

    @staticmethod
    def pnum(person_id: str) -> int:
        return int(person_id[person_id.rindex(":p") + 2:])

    def set(self, wf: str, p: int, code: int) -> None:
        a = self.arr.get(wf)
        if a is None or p >= len(a):
            n = max(1024, (p + 1) * 2 if a is None else max(len(a) * 2, p + 1))
            b = np.zeros(n, dtype=np.int32)
            if a is not None:
                b[: len(a)] = a
            self.arr[wf] = a = b
        a[p] = code

    def get(self, wf: str, p: int) -> int:
        a = self.arr.get(wf)
        return int(a[p]) if a is not None and p < len(a) else 0


class Ingestor:
    def __init__(self, api, store: Store, store_calls: bool = True):
        self.api, self.store = api, store
        self.codes = Codes(store)
        self.persons = PersonIndex(store)
        self.store_calls = store_calls
        self.total_events = int(store.q1("SELECT COALESCE(SUM(events),0) FROM chunks_done") or 0)
        self.total_wall = float(store.q1("SELECT COALESCE(SUM(wall_s),0) FROM chunks_done") or 0.0)

    def last_chunk(self) -> int:
        v = self.store.q1("SELECT MAX(chunk) FROM chunks_done")
        return -1 if v is None else int(v)

    def pending(self) -> list[dict]:
        after = self.last_chunk()
        metas = self.api.list_chunks("history", after) + self.api.list_chunks("events", after)
        return sorted(metas, key=lambda m: m["chunk"])

    def run(self, on_world_event=None) -> dict:
        """Ingest every chunk we haven't committed yet. Returns throughput stats for this call."""
        n_ev, t0, chunks = 0, time.time(), 0
        for meta in self.pending():
            if self.store.q1("SELECT 1 FROM chunks_done WHERE chunk=?", (meta["chunk"],)):
                continue
            text = self.api.chunk_text(meta["chunk"])
            evs = self._process(meta, text, on_world_event)
            n_ev += evs
            chunks += 1
        dt = time.time() - t0
        return {"events": n_ev, "chunks": chunks, "wall_s": dt}

    # ------------------------------------------------------------------ one chunk
    def _process(self, meta: dict, text: str, on_world_event) -> int:
        t0 = time.time()
        eng: dict[tuple, list] = {}
        pick: dict[tuple, list] = {}
        qa: dict[tuple, list] = {}
        leads: dict[tuple, list] = {}
        new_persons: list[tuple] = []
        heard: list[tuple] = []
        world: list[dict] = []
        camp_day: dict[str, int] = {}
        loads = json.loads
        codes, persons = self.codes, self.persons
        n = 0
        with self.store.txn():
            for line in text.splitlines():
                if not line:
                    continue
                ev = loads(line)
                n += 1
                t = ev["type"]
                if t == "call":
                    wf = ev["workflow_id"]
                    m = minute_of(ev["ts"])
                    day, hour = m // 1440, (m % 1440) // 60
                    pid = ev["person_id"]
                    code = persons.get(wf, PersonIndex.pnum(pid))
                    v = ev["variant"]
                    conn = ev["connected"]
                    k = (wf, day, hour, code, v["caller_id"])
                    c = pick.get(k)
                    if c is None:
                        pick[k] = [1, 1 if conn else 0]
                    else:
                        c[0] += 1
                        c[1] += 1 if conn else 0
                    if conn:
                        e = 1 if ev["engaged"] else 0
                        k = (wf, day, ev["config_version"], ev["cohort_id"], code, v["welcome_message"], v["voice"])
                        c = eng.get(k)
                        if c is None:
                            eng[k] = [1, e]
                        else:
                            c[0] += 1
                            c[1] += e
                        f = 1 if (ev.get("qa") or {}).get("hallucination_flag") else 0
                        k = (wf, m // 30, v["prompt_version"])
                        c = qa.get(k)
                        if c is None:
                            qa[k] = [1, f, e]
                        else:
                            c[0] += 1
                            c[1] += f
                            c[2] += e
                        if e:
                            k = (wf, ev["campaign_id"], code)
                            c = leads.get(k)
                            if c is None:
                                leads[k] = [0, 1, None]
                            else:
                                c[1] += 1
                        if self.store_calls:
                            heard.append((ev["event_id"], wf, m, ev["lead_id"], pid, ev["campaign_id"],
                                          ev["config_version"], ev["cohort_id"], v["welcome_message"], v["voice"],
                                          v["caller_id"], v["prompt_version"], e, f))
                elif t == "lead":
                    wf = ev["workflow_id"]
                    code = codes.get(ev["features"])
                    p = PersonIndex.pnum(ev["person_id"])
                    if persons.get(wf, p) != code:
                        persons.set(wf, p, code)
                        new_persons.append((wf, p, code))
                    cd = camp_day.get(ev["campaign_id"])
                    if cd is None:
                        cd = camp_day[ev["campaign_id"]] = minute_of(ev["ts"]) // 1440
                    k = (wf, ev["campaign_id"], code)
                    c = leads.get(k)
                    if c is None:
                        leads[k] = [1, 0, cd]
                    else:
                        c[0] += 1
                        c[2] = cd
                else:
                    world.append(ev)
            db = self.store.db
            db.executemany("INSERT OR REPLACE INTO persons VALUES (?,?,?)", new_persons)
            db.executemany(
                "INSERT INTO agg_eng VALUES (?,?,?,?,?,?,?,?,?) ON CONFLICT DO UPDATE SET "
                "conn=conn+excluded.conn, eng=eng+excluded.eng", [(*k, *v) for k, v in eng.items()])
            db.executemany(
                "INSERT INTO agg_pick VALUES (?,?,?,?,?,?,?) ON CONFLICT DO UPDATE SET "
                "dials=dials+excluded.dials, conn=conn+excluded.conn", [(*k, *v) for k, v in pick.items()])
            db.executemany(
                "INSERT INTO agg_qa VALUES (?,?,?,?,?,?) ON CONFLICT DO UPDATE SET "
                "conn=conn+excluded.conn, flags=flags+excluded.flags, eng=eng+excluded.eng",
                [(*k, *v) for k, v in qa.items()])
            db.executemany(
                "INSERT INTO campaign_leads VALUES (?,?,COALESCE(?, -999),?,?,?) ON CONFLICT DO UPDATE SET "
                "uploaded=uploaded+excluded.uploaded, concluded=concluded+excluded.concluded, "
                "cday=CASE WHEN excluded.cday=-999 THEN cday ELSE excluded.cday END",
                [(k[0], k[1], v[2], k[2], v[0], v[1]) for k, v in leads.items()])
            if heard:
                db.executemany("INSERT OR IGNORE INTO calls_heard VALUES (?,?,?,?,?,?,?,?,?,?,?,?,?,?)", heard)
            for ev in world:
                db.execute("INSERT OR IGNORE INTO world_events VALUES (?,?,?,?,?)",
                           (ev["event_id"], ev["type"], ev.get("workflow_id"), minute_of(ev["ts"]),
                            json.dumps(ev)))
                if on_world_event:
                    on_world_event(ev)
            wall = time.time() - t0
            db.execute("INSERT INTO chunks_done VALUES (?,?,?,?,?,?,?,datetime('now'))",
                       (meta["chunk"], meta["kind"], n, meta.get("first_event_id"), meta.get("last_event_id"),
                        meta.get("until_minute"), wall))
        self.total_events += n
        self.total_wall += wall
        log.debug("chunk %s: %d events in %.2fs", meta["chunk"], n, wall)
        return n
