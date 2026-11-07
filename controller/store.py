"""SQLite store: the controller's only state."""
from __future__ import annotations

import contextlib
import json
import sqlite3
from pathlib import Path

SCHEMA = """
CREATE TABLE IF NOT EXISTS meta (key TEXT PRIMARY KEY, value TEXT);

-- workflow policies as the API returned them (for audit: what policy was in force)
CREATE TABLE IF NOT EXISTS workflows (workflow_id TEXT PRIMARY KEY, tenant_id TEXT, body TEXT);

-- ---------------------------------------------------------------- ingestion (one txn per chunk)
CREATE TABLE IF NOT EXISTS chunks_done (chunk INTEGER PRIMARY KEY, kind TEXT, events INTEGER,
    first_event_id INTEGER, last_event_id INTEGER, until_minute INTEGER, wall_s REAL, done_at TEXT);
CREATE TABLE IF NOT EXISTS codes (code_id INTEGER PRIMARY KEY, lang TEXT, city_tier TEXT, age_band TEXT,
    value_band TEXT, UNIQUE (lang, city_tier, age_band, value_band));
CREATE TABLE IF NOT EXISTS persons (workflow_id TEXT, pnum INTEGER, code_id INTEGER,
    PRIMARY KEY (workflow_id, pnum)) WITHOUT ROWID;
CREATE TABLE IF NOT EXISTS campaign_leads (workflow_id TEXT, campaign_id TEXT, cday INTEGER, code_id INTEGER,
    uploaded INTEGER DEFAULT 0, concluded INTEGER DEFAULT 0,
    PRIMARY KEY (workflow_id, campaign_id, code_id)) WITHOUT ROWID;
-- engagement evidence: connected calls by stratum x lead features x arm
CREATE TABLE IF NOT EXISTS agg_eng (workflow_id TEXT, day INTEGER, version INTEGER, cohort TEXT, code_id INTEGER,
    wm TEXT, vo TEXT, conn INTEGER, eng INTEGER,
    PRIMARY KEY (workflow_id, day, version, cohort, code_id, wm, vo)) WITHOUT ROWID;
-- pickup evidence: dials by hour x lead features x caller ID
CREATE TABLE IF NOT EXISTS agg_pick (workflow_id TEXT, day INTEGER, hour INTEGER, code_id INTEGER, did TEXT,
    dials INTEGER, conn INTEGER,
    PRIMARY KEY (workflow_id, day, hour, code_id, did)) WITHOUT ROWID;
-- safety evidence: connected calls by 30-min slot x prompt
CREATE TABLE IF NOT EXISTS agg_qa (workflow_id TEXT, slot INTEGER, prompt TEXT, conn INTEGER, flags INTEGER,
    eng INTEGER, PRIMARY KEY (workflow_id, slot, prompt)) WITHOUT ROWID;
-- what each customer actually heard (connected calls only) -- the compliance question
CREATE TABLE IF NOT EXISTS calls_heard (event_id INTEGER PRIMARY KEY, workflow_id TEXT, minute INTEGER,
    lead_id TEXT, person_id TEXT, campaign_id TEXT, version INTEGER, cohort TEXT, wm TEXT, vo TEXT, did TEXT,
    prompt TEXT, engaged INTEGER, halluc_flag INTEGER);
CREATE INDEX IF NOT EXISTS calls_heard_person ON calls_heard (person_id, minute);
-- non-call events kept verbatim (config changes, approval decisions, campaigns)
CREATE TABLE IF NOT EXISTS world_events (event_id INTEGER PRIMARY KEY, type TEXT, workflow_id TEXT,
    minute INTEGER, body TEXT);

-- ---------------------------------------------------------------- what the controller knows and decided
CREATE TABLE IF NOT EXISTS configs (workflow_id TEXT, version INTEGER, actor TEXT, applied_at TEXT,
    config TEXT, PRIMARY KEY (workflow_id, version));
CREATE TABLE IF NOT EXISTS cohorts (workflow_id TEXT, cohort_id TEXT, where_json TEXT, purpose TEXT,
    status TEXT, created_minute INTEGER, reason TEXT, PRIMARY KEY (workflow_id, cohort_id));
CREATE TABLE IF NOT EXISTS experiments (workflow_id TEXT, alloc_key TEXT, dim TEXT, state TEXT,
    updated_minute INTEGER, PRIMARY KEY (workflow_id, alloc_key, dim));
CREATE TABLE IF NOT EXISTS dids (workflow_id TEXT, did TEXT, status TEXT, since_minute INTEGER, note TEXT,
    PRIMARY KEY (workflow_id, did));
CREATE TABLE IF NOT EXISTS frozen_dims (workflow_id TEXT, dim TEXT, until_minute INTEGER, sticky INTEGER,
    reason TEXT, PRIMARY KEY (workflow_id, dim));
CREATE TABLE IF NOT EXISTS incidents (incident_id TEXT PRIMARY KEY, workflow_id TEXT, kind TEXT, status TEXT,
    opened_minute INTEGER, closed_minute INTEGER, detail TEXT);
CREATE TABLE IF NOT EXISTS proposals (proposal_id TEXT PRIMARY KEY, workflow_id TEXT, channel TEXT,
    status TEXT, purpose TEXT, base_version INTEGER, created_minute INTEGER, submitted_minute INTEGER,
    decided_minute INTEGER, applied_minute INTEGER, approval_id TEXT, applied_version INTEGER,
    parent_id TEXT, dims TEXT, body TEXT, reasons TEXT, note TEXT);
CREATE INDEX IF NOT EXISTS proposals_wf ON proposals (workflow_id, status);
-- append-only audit log: every detection, analysis, decision and API outcome, in plain words + JSON
CREATE TABLE IF NOT EXISTS decisions (id INTEGER PRIMARY KEY AUTOINCREMENT, minute INTEGER, workflow_id TEXT,
    kind TEXT, summary TEXT, detail TEXT, proposal_id TEXT, wall_ts TEXT DEFAULT (datetime('now')));
CREATE INDEX IF NOT EXISTS decisions_wf ON decisions (workflow_id, minute);
CREATE TABLE IF NOT EXISTS metrics (minute INTEGER, name TEXT, value REAL, PRIMARY KEY (minute, name))
    WITHOUT ROWID;
CREATE TABLE IF NOT EXISTS alerts (id INTEGER PRIMARY KEY AUTOINCREMENT, minute INTEGER, severity TEXT,
    workflow_id TEXT, summary TEXT, action TEXT);
"""


class Store:
    def __init__(self, path: str | Path):
        self.path = str(path)
        Path(self.path).parent.mkdir(parents=True, exist_ok=True)
        self.db = sqlite3.connect(self.path, isolation_level=None, check_same_thread=False)
        self.db.execute("PRAGMA journal_mode=WAL")
        self.db.execute("PRAGMA synchronous=NORMAL")
        self.db.execute("PRAGMA foreign_keys=OFF")
        self.db.executescript(SCHEMA)
        self._depth = 0

    # ------------------------------------------------------------------ transactions
    @contextlib.contextmanager
    def txn(self):
        """Nested-safe transaction. Only the outermost level commits."""
        if self._depth == 0:
            self.db.execute("BEGIN IMMEDIATE")
        self._depth += 1
        try:
            yield self.db
        except BaseException:
            self._depth -= 1
            if self._depth == 0:
                self.db.execute("ROLLBACK")
            raise
        else:
            self._depth -= 1
            if self._depth == 0:
                self.db.execute("COMMIT")

    def q(self, sql: str, args=()) -> list[tuple]:
        return self.db.execute(sql, args).fetchall()

    def q1(self, sql: str, args=()):
        r = self.db.execute(sql, args).fetchone()
        return r[0] if r else None

    def x(self, sql: str, args=()):
        return self.db.execute(sql, args)

    # ------------------------------------------------------------------ meta
    def get_meta(self, key: str, default=None):
        v = self.q1("SELECT value FROM meta WHERE key=?", (key,))
        return default if v is None else json.loads(v)

    def set_meta(self, key: str, value) -> None:
        self.x("INSERT INTO meta(key, value) VALUES(?,?) ON CONFLICT(key) DO UPDATE SET value=excluded.value",
               (key, json.dumps(value)))

    # ------------------------------------------------------------------ audit
    def decide(self, minute: int, wf: str | None, kind: str, summary: str, detail=None,
               proposal_id: str | None = None) -> None:
        self.x("INSERT INTO decisions(minute, workflow_id, kind, summary, detail, proposal_id) VALUES(?,?,?,?,?,?)",
               (minute, wf, kind, summary, json.dumps(detail, default=str) if detail is not None else None,
                proposal_id))

    def metric(self, minute: int, name: str, value: float) -> None:
        self.x("INSERT INTO metrics(minute, name, value) VALUES(?,?,?) "
               "ON CONFLICT(minute, name) DO UPDATE SET value=excluded.value", (minute, name, float(value)))

    def alert(self, minute: int, severity: str, wf: str | None, summary: str, action: str) -> None:
        recent = self.q1("SELECT COUNT(*) FROM alerts WHERE summary=? AND minute > ?", (summary, minute - 360))
        if not recent:   # de-duplicate: the same alert at most once per 6 sim-hours
            self.x("INSERT INTO alerts(minute, severity, workflow_id, summary, action) VALUES(?,?,?,?,?)",
                   (minute, severity, wf, summary, action))
