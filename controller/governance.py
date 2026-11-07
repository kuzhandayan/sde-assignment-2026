"""Governance client (C9): the only code that changes a workflow's config.

Proposal state machine (table `proposals`, one row per proposal_id):

  approval channel:  submitting -> pending -> approved -> applying -> applied
                                      |          |           |
                                      |          |           +-> stale   (config changed under us: re-plan)
                                      |          +-> lapsed            (apply window missed: re-plan)
                                      |          +-> stale             (we saw a newer version before applying)
                                      +-> rejected | expired           (re-plan with fresh data, never resubmit)
                     submitting -> failed | abandoned  (refused at submit, or crash before we know it was sent)
  auto channel:      submitting -> applied | refused | stale | failed | abandoned

Crash safety: the row is written (status 'submitting'/'applying') BEFORE the HTTP call, inside its own
transaction. On restart `reconcile()` asks the simulator what really happened (list approvals by proposal_id,
config history by proposal_id/approval_id) and moves the row to the true state. proposal_id is the
simulator's idempotency key, so a retried POST can never create a second request.
"""
from __future__ import annotations

import json
import logging

from . import settings as S
from .simtime import minute_of

log = logging.getLogger("controller.gov")
INFLIGHT = ("submitting", "pending", "approved", "applying")


class Governance:
    def __init__(self, ctx):
        self.ctx = ctx
        self.store, self.api = ctx.store, ctx.api

    # ------------------------------------------------------------------ budget & timing
    def rows(self, wf: str, statuses=None) -> list[dict]:
        sql = "SELECT proposal_id, channel, status, purpose, base_version, created_minute, submitted_minute, " \
              "decided_minute, applied_minute, approval_id, applied_version, parent_id, dims, reasons " \
              "FROM proposals WHERE workflow_id=?"
        args = [wf]
        if statuses:
            sql += f" AND status IN ({','.join('?' * len(statuses))})"
            args += list(statuses)
        cols = ["proposal_id", "channel", "status", "purpose", "base_version", "created_minute",
                "submitted_minute", "decided_minute", "applied_minute", "approval_id", "applied_version",
                "parent_id", "dims", "reasons"]
        return [dict(zip(cols, r)) for r in self.store.q(sql + " ORDER BY created_minute", args)]

    def inflight(self, wf: str, channel: str = "approval") -> list[dict]:
        return [r for r in self.rows(wf, INFLIGHT) if r["channel"] == channel]

    def used_24h(self, wf: str, now: int, purpose: str | None = None) -> int:
        sql = "SELECT COUNT(*) FROM proposals WHERE workflow_id=? AND channel='approval' AND submitted_minute > ? " \
              "AND status NOT IN ('failed','abandoned')"
        args = [wf, now - 1440]
        if purpose:
            sql += " AND purpose=?"
            args.append(purpose)
        return int(self.store.q1(sql, args) or 0)

    def can_submit(self, wf: str, now: int, urgent: bool) -> tuple[bool, str]:
        g = self.ctx.wfs[wf]["governance"]
        limit = int(g["max_requests_per_24h"])
        used = self.used_24h(wf, now)
        if used >= limit:
            return False, f"approver fatigue budget used ({used}/{limit} in 24h)"
        if urgent:
            return True, "incident"
        reserve = S.INCIDENT_SLOTS_RESERVED if limit > 1 else 0
        if used >= limit - reserve:
            return False, f"keeping {reserve} request(s) per 24h free for incidents ({used}/{limit} used)"
        prefs = S.TENANT_PREFS.get(self.ctx.wfs[wf]["tenant_id"], {})
        routine = self.used_24h(wf, now, "routine")
        if routine >= prefs.get("max_routine_requests_per_day", 99):
            return False, "tenant's own daily request preference reached"
        lo, hi = g["approver_hours"]
        lo = max(lo, prefs.get("earliest_submit_hour", lo))
        mod = now % 1440
        if not (lo * 60 <= mod <= hi * 60 - S.SUBMIT_END_MARGIN_MIN):
            return False, f"outside routine submit window {lo:02d}:00-{hi:02d}:00 minus margin"
        return True, "ok"

    # ------------------------------------------------------------------ submit
    def _new_id(self, wf: str, purpose: str) -> str:
        n = int(self.store.q1("SELECT COUNT(*) FROM proposals WHERE workflow_id=? AND created_minute=?",
                              (wf, self.ctx.now)) or 0)
        return f"{wf}.{purpose}.m{self.ctx.now}.{n + 1}"

    def submit(self, wf: str, body: dict, purpose: str, dims: list[str], parent: str | None = None) -> dict:
        """POST /approvals. body has everything except proposal_id/workflow_id. Returns the row."""
        pid = self._new_id(wf, purpose)
        body = {"proposal_id": pid, "workflow_id": wf, **body}
        with self.store.txn():
            self.store.x("INSERT INTO proposals (proposal_id, workflow_id, channel, status, purpose, base_version, "
                         "created_minute, submitted_minute, parent_id, dims, body) "
                         "VALUES (?,?,?,?,?,?,?,?,?,?,?)",
                         (pid, wf, "approval", "submitting", purpose, body["base_version"], self.ctx.now,
                          self.ctx.now, parent, json.dumps(dims), json.dumps(body)))
            self.store.decide(self.ctx.now, wf, "proposal.submit", body["change_summary"],
                              {"dims": dims, "impact_score": body["impact_score"],
                               "affected_leads": body["affected_leads"]}, pid)
        r = self.api.request_approval(body)
        with self.store.txn():
            if r.ok:
                self.store.x("UPDATE proposals SET status='pending', approval_id=? WHERE proposal_id=?",
                             (r.body["approval_id"], pid))
                self.store.decide(self.ctx.now, wf, "proposal.pending",
                                  f"{r.body['approval_id']} pending, expires {r.body.get('expires_at')}", r.body, pid)
            elif r.status == 409 and r.error == "duplicate_proposal_id":
                self._reconcile_one(wf, pid)
            else:
                st = "stale" if r.error == "stale_base_version" else "failed"
                self.store.x("UPDATE proposals SET status=?, reasons=? WHERE proposal_id=?",
                             (st, json.dumps(r.body), pid))
                self.store.decide(self.ctx.now, wf, f"proposal.{st}", f"refused at submit: {r.body}", r.body, pid)
        return self.get(pid)

    def auto(self, wf: str, body: dict, purpose: str, dims: list[str]) -> dict:
        """PUT /workflows/{wf}/config (policy-permitted auto-apply)."""
        pid = self._new_id(wf, purpose)
        body = {"proposal_id": pid, **body}
        with self.store.txn():
            self.store.x("INSERT INTO proposals (proposal_id, workflow_id, channel, status, purpose, base_version, "
                         "created_minute, submitted_minute, dims, body) VALUES (?,?,?,?,?,?,?,?,?,?)",
                         (pid, wf, "auto", "submitting", purpose, body["base_version"], self.ctx.now, self.ctx.now,
                          json.dumps(dims), json.dumps(body)))
            self.store.decide(self.ctx.now, wf, "auto.submit", body.get("change_summary") or body["rationale"],
                              {"dims": dims}, pid)
        r = self.api.auto_apply(wf, {k: body[k] for k in ("proposal_id", "base_version", "proposed_config",
                                                           "rationale", "evidence") if k in body})
        with self.store.txn():
            if r.ok:
                self._mark_applied(wf, pid, r.body["version"])
            elif r.status == 409 and r.error == "duplicate_proposal_id":
                self._reconcile_one(wf, pid)
            else:
                st = {"stale_base_version": "stale", "auto_apply_not_permitted": "refused"}.get(r.error, "failed")
                self.store.x("UPDATE proposals SET status=?, reasons=? WHERE proposal_id=?",
                             (st, json.dumps(r.body), pid))
                self.store.decide(self.ctx.now, wf, f"auto.{st}", f"auto-apply {st}: {r.body}", r.body, pid)
        return self.get(pid)

    def get(self, pid: str) -> dict:
        r = self.store.q("SELECT workflow_id FROM proposals WHERE proposal_id=?", (pid,))
        return next(x for x in self.rows(r[0][0]) if x["proposal_id"] == pid)

    def _mark_applied(self, wf: str, pid: str, version: int) -> None:
        self.store.x("UPDATE proposals SET status='applied', applied_minute=?, applied_version=? WHERE proposal_id=?",
                     (self.ctx.now, version, pid))
        dims = json.loads(self.store.q1("SELECT dims FROM proposals WHERE proposal_id=?", (pid,)) or "[]")
        # an approved change on a dim ends the supervisor's 'sticky' hold on it
        ch = self.store.q1("SELECT channel FROM proposals WHERE proposal_id=?", (pid,))
        if ch == "approval":
            for d in dims:
                self.store.x("DELETE FROM frozen_dims WHERE workflow_id=? AND dim=? AND until_minute<=?",
                             (wf, d, self.ctx.now))
        self.ctx.refresh_config(wf)
        self.store.decide(self.ctx.now, wf, "proposal.applied", f"applied as config v{version} (dims {dims})",
                          {"version": version}, pid)

    # ------------------------------------------------------------------ poll / apply
    def poll(self) -> None:
        for wf in self.ctx.wfs:
            rows = self.inflight(wf)
            if not rows:
                continue
            remote = {a["proposal_id"]: a for a in self.api.list_approvals(wf)}
            for row in rows:
                a = remote.get(row["proposal_id"])
                if a is None:
                    continue
                self._sync(wf, row, a)

    def _sync(self, wf: str, row: dict, a: dict) -> None:
        pid, st = row["proposal_id"], a["status"]
        dec = minute_of(a["decided_at"]) if a.get("decided_at") else None
        with self.store.txn():
            if st in ("rejected", "expired") and row["status"] != st:
                self.store.x("UPDATE proposals SET status=?, decided_minute=?, reasons=? WHERE proposal_id=?",
                             (st, dec if dec is not None else self.ctx.now, json.dumps(a.get("reasons", [])), pid))
                self.store.decide(self.ctx.now, wf, f"proposal.{st}",
                                  f"{a['approval_id']} {st}" + (f": {'; '.join(a['reasons'])}" if a.get("reasons")
                                                                 else ""), a, pid)
                if st == "rejected" and any("validation" in r or "evidence" in r for r in a.get("reasons", [])):
                    self.store.alert(self.ctx.now, "ticket", wf, f"{wf}: proposal rejected for evidence",
                                     f"see proposal {pid}")
            elif st == "applied" and row["status"] != "applied":
                self._mark_applied(wf, pid, self._applied_version(wf, a["approval_id"]))
            elif st == "lapsed":
                self.store.x("UPDATE proposals SET status='lapsed' WHERE proposal_id=?", (pid,))
                self.store.decide(self.ctx.now, wf, "proposal.lapsed", "apply window missed", a, pid)
                self.store.alert(self.ctx.now, "ticket", wf, f"{wf}: approved change lapsed",
                                 "controller missed the apply window; check loop lag")
            elif st == "approved":
                if row["status"] == "pending":
                    self.store.x("UPDATE proposals SET status='approved', decided_minute=? WHERE proposal_id=?",
                                 (dec, pid))
                    self.store.decide(self.ctx.now, wf, "proposal.approved",
                                      f"{a['approval_id']} approved at {a.get('decided_at')}, apply by "
                                      f"{a.get('apply_by')}", a, pid)
        if st == "approved":
            self._apply(wf, pid, a["approval_id"], row["base_version"])

    def _apply(self, wf: str, pid: str, aid: str, base_version: int) -> None:
        cur = self.ctx.refresh_config(wf)
        if cur["version"] != base_version:
            with self.store.txn():
                self.store.x("UPDATE proposals SET status='stale' WHERE proposal_id=?", (pid,))
                self.store.decide(self.ctx.now, wf, "proposal.stale",
                                  f"{aid} approved but config moved v{base_version} -> v{cur['version']} "
                                  f"({cur['actor']}); not applying, will re-plan on fresh data",
                                  {"current": cur["version"], "actor": cur["actor"]}, pid)
            return
        with self.store.txn():
            self.store.x("UPDATE proposals SET status='applying' WHERE proposal_id=?", (pid,))
        r = self.api.apply(wf, aid)
        with self.store.txn():
            if r.ok:
                self._mark_applied(wf, pid, r.body["version"])
            elif r.status == 409 and r.error == "stale_base_version":
                self.store.x("UPDATE proposals SET status='stale' WHERE proposal_id=?", (pid,))
                self.store.decide(self.ctx.now, wf, "proposal.stale", f"apply refused: {r.body}", r.body, pid)
            elif r.status == 410:
                self.store.x("UPDATE proposals SET status='lapsed' WHERE proposal_id=?", (pid,))
                self.store.decide(self.ctx.now, wf, "proposal.lapsed", "apply window missed", r.body, pid)
            elif r.status == 409 and r.error == "not_approved":
                self._reconcile_one(wf, pid)
            else:
                self.store.x("UPDATE proposals SET status='approved' WHERE proposal_id=?", (pid,))
                log.warning("apply %s failed: %s (will retry)", pid, r)

    def _applied_version(self, wf: str, aid: str) -> int | None:
        for v in self.api.config_history(wf):
            if v.get("approval_id") == aid:
                return v["version"]
        return None

    # ------------------------------------------------------------------ crash recovery
    def _reconcile_one(self, wf: str, pid: str) -> None:
        row = self.get(pid)
        if row["channel"] == "approval":
            a = next((x for x in self.api.list_approvals(wf) if x["proposal_id"] == pid), None)
            if a is None:
                self.store.x("UPDATE proposals SET status='abandoned' WHERE proposal_id=?", (pid,))
                self.store.decide(self.ctx.now, wf, "proposal.abandoned",
                                  "never reached the simulator before a crash; the planner will decide again on "
                                  "fresh data", None, pid)
                return
            self.store.x("UPDATE proposals SET approval_id=?, status=? WHERE proposal_id=?",
                         (a["approval_id"], {"applied": "applying"}.get(a["status"], a["status"]), pid))
            if a["status"] == "applied":
                self._mark_applied(wf, pid, self._applied_version(wf, a["approval_id"]))
        else:
            hist = self.api.config_history(wf)
            v = next((h["version"] for h in hist if h.get("proposal_id") == pid), None)
            if v is not None:
                self._mark_applied(wf, pid, v)
            else:
                self.store.x("UPDATE proposals SET status='abandoned' WHERE proposal_id=?", (pid,))
                self.store.decide(self.ctx.now, wf, "auto.abandoned", "auto-apply never landed before a crash",
                                  None, pid)

    def reconcile(self) -> None:
        """Run once at start-up: make every in-flight row agree with the simulator."""
        for wf in self.ctx.wfs:
            for row in self.rows(wf, ("submitting", "applying")):
                with self.store.txn():
                    if row["status"] == "submitting":
                        self._reconcile_one(wf, row["proposal_id"])
                    else:
                        v = self._applied_version(wf, row["approval_id"])
                        if v is not None:
                            self._mark_applied(wf, row["proposal_id"], v)
                        else:
                            self.store.x("UPDATE proposals SET status='approved' WHERE proposal_id=?",
                                         (row["proposal_id"],))
            self.store.decide(self.ctx.now, wf, "recovery.reconciled",
                              f"in-flight proposals after restart: "
                              f"{[(r['proposal_id'], r['status']) for r in self.inflight(wf)]}", None)
        self.poll()
