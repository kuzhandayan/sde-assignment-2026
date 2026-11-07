"""Audit queries (C12), answered only from the controller's own store."""
from __future__ import annotations

import json
import sqlite3

from .simtime import label, parse_label


def _db(path):
    db = sqlite3.connect(f"file:{path}?mode=ro", uri=True)
    db.row_factory = sqlite3.Row
    return db


def _kpis(db, wf, lo, hi):
    lo_d, hi_d = lo // 1440, hi // 1440
    p = db.execute("SELECT COALESCE(SUM(dials),0) d, COALESCE(SUM(conn),0) c FROM agg_pick WHERE workflow_id=? AND "
                   "(day*24+hour) >= ? AND (day*24+hour) < ? AND day BETWEEN ? AND ?",
                   (wf, lo // 60, hi // 60, lo_d, hi_d)).fetchone()
    e = db.execute("SELECT COALESCE(SUM(conn),0) c, COALESCE(SUM(eng),0) e, COALESCE(SUM(flags),0) f FROM agg_qa "
                   "WHERE workflow_id=? AND slot>=? AND slot<?", (wf, lo // 30, hi // 30)).fetchone()
    return {"dials": p["d"], "pickup_rate": round(p["c"] / p["d"], 4) if p["d"] else None,
            "connected": e["c"], "engagement_rate": round(e["e"] / e["c"], 4) if e["c"] else None,
            "hallucination_flag_rate": round(e["f"] / e["c"], 4) if e["c"] else None}


def change_record(db, wf: str, version: int) -> dict:
    ev = db.execute("SELECT minute, body FROM world_events WHERE workflow_id=? AND type='config_changed' AND "
                    "json_extract(body,'$.version')=?", (wf, version)).fetchone()
    if not ev:
        return {"version": version, "note": "no config_changed event for this version in the store"}
    b = json.loads(ev["body"])
    out = {"version": version, "at": label(ev["minute"]), "minute": ev["minute"], "actor": b["actor"],
           "changed_dims": b["changed_dims"], "proposal_id": b.get("proposal_id"), "approval_id": b.get("approval_id")}
    if b["actor"] == "supervisor":
        out["who"] = "client supervisor (direct edit, outside governance)"
    elif b["actor"] == "controller_auto":
        wfrow = db.execute("SELECT body FROM workflows WHERE workflow_id=?", (wf,)).fetchone()
        pol = json.loads(wfrow["body"])["governance"]["auto_apply"] if wfrow else {}
        out["who"] = (f"auto-applied by the controller under the signed policy (auto_apply allowed_dims="
                      f"{pol.get('allowed_dims')}, max_shift={pol.get('max_shift')})")
    elif b["actor"] == "controller_approved":
        out["who"] = f"client approver via approval {b.get('approval_id')}"
    pr = db.execute("SELECT * FROM proposals WHERE proposal_id=?", (b.get("proposal_id"),)).fetchone() \
        if b.get("proposal_id") else None
    if pr:
        body = json.loads(pr["body"])
        out["proposal"] = {"proposal_id": pr["proposal_id"], "purpose": pr["purpose"], "channel": pr["channel"],
                           "submitted": label(pr["submitted_minute"]),
                           "decided": label(pr["decided_minute"]) if pr["decided_minute"] is not None else None,
                           "change_summary": body.get("change_summary"), "rationale": body.get("rationale"),
                           "impact_score": body.get("impact_score"), "affected_leads": body.get("affected_leads"),
                           "diff": body.get("diff"), "dry_run": body.get("dry_run"), "evidence": body.get("evidence")}
        trail = db.execute("SELECT minute, kind, summary FROM decisions WHERE proposal_id=? ORDER BY id",
                           (pr["proposal_id"],)).fetchall()
        out["lifecycle"] = [f"{label(r['minute'])} {r['kind']}: {r['summary']}" for r in trail]
    m = ev["minute"]
    out["evidence_before"] = [f"{label(r['minute'])} {r['kind']}: {r['summary']}" for r in db.execute(
        "SELECT minute, kind, summary FROM decisions WHERE workflow_id=? AND minute BETWEEN ? AND ? AND kind IN "
        "('experiment.promote','experiment.drop','experiment.rollback','cohort.segment_added','callerid.degraded',"
        "'callerid.probe_passed','callerid.probe_failed','incident.opened','incident.validation',"
        "'guardrail.engagement','schedule.rollback','supervisor.edit') ORDER BY id", (wf, m - 1440, m)).fetchall()]
    out["kpis_24h_before"] = _kpis(db, wf, m - 1440, m)
    out["kpis_24h_after"] = _kpis(db, wf, m, m + 1440)
    nxt = db.execute("SELECT minute, body FROM world_events WHERE workflow_id=? AND type='config_changed' AND "
                     "json_extract(body,'$.version')=?", (wf, version + 1)).fetchone()
    if nxt:
        nb = json.loads(nxt["body"])
        out["next_change"] = f"v{version + 1} at {label(nxt['minute'])} by {nb['actor']} ({', '.join(nb['changed_dims'])})"
    out["after"] = [f"{label(r['minute'])} {r['kind']}: {r['summary']}" for r in db.execute(
        "SELECT minute, kind, summary FROM decisions WHERE workflow_id=? AND minute > ? AND minute <= ? AND kind IN "
        "('experiment.rollback','experiment.promote','incident.verified','incident.fix_live','schedule.rollback',"
        "'guardrail.engagement','callerid.degraded','supervisor.edit') ORDER BY id LIMIT 10", (wf, m, m + 2 * 1440)
    ).fetchall()]
    return out


def why(path: str, wf: str, at: str, as_json: bool = False) -> str:
    db = _db(path)
    t = parse_label(at)
    # the change applied closest to (and not after) T + 15 min; plus anything else within the hour
    rows = db.execute("SELECT minute, json_extract(body,'$.version') v FROM world_events WHERE workflow_id=? AND "
                      "type='config_changed' AND minute <= ? ORDER BY minute DESC, event_id DESC LIMIT 1",
                      (wf, t + 15)).fetchall()
    if not rows:
        return f"no config change for {wf} at or before {label(t)}; v1 (business default) was live"
    rec = change_record(db, wf, rows[0]["v"])
    if as_json:
        return json.dumps(rec, indent=2, default=str)
    L = [f"# {wf} — config v{rec['version']} applied {rec['at']} (asked about {label(t)})", "",
         f"**Who:** {rec.get('who')}", f"**Changed:** {', '.join(rec['changed_dims'])}"]
    p = rec.get("proposal")
    if p:
        L += [f"**Request:** {p['proposal_id']} ({p['purpose']}, via {p['channel']}), submitted {p['submitted']}"
              + (f", decided {p['decided']}" if p.get("decided") else ""),
              f"**Summary:** {p['change_summary']}", f"**Why:** {p['rationale']}",
              f"**Impact score:** {p['impact_score']}  ·  **Affected leads:** {p['affected_leads']}",
              "", "**Diff:**", "```json", json.dumps(p["diff"], indent=1)[:3000], "```",
              "**Dry run:**", "```json", json.dumps(p["dry_run"], indent=1)[:3000], "```",
              "**Lifecycle:**"] + [f"- {x}" for x in rec.get("lifecycle", [])]
    if rec["evidence_before"]:
        L += ["", "**Evidence in the 24h before:**"] + [f"- {x}" for x in rec["evidence_before"]]
    L += ["", f"**KPIs 24h before:** {rec['kpis_24h_before']}", f"**KPIs 24h after:** {rec['kpis_24h_after']}"]
    if rec.get("next_change"):
        L.append(f"**Next change:** {rec['next_change']}")
    if rec["after"]:
        L += ["", "**What happened next (48h):**"] + [f"- {x}" for x in rec["after"]]
    return "\n".join(L)


def heard(path: str, person: str, day: int | None = None) -> str:
    """For compliance (stakeholders/02): what a customer heard, and why that variant was live."""
    db = _db(path)
    sql = "SELECT * FROM calls_heard WHERE person_id=?"
    args = [person]
    if day is not None:
        sql += " AND minute >= ? AND minute < ?"
        args += [day * 1440, (day + 1) * 1440]
    rows = db.execute(sql + " ORDER BY minute", args).fetchall()
    if not rows:
        return f"no connected calls for {person} in the store"
    L = [f"# What {person} heard", ""]
    for r in rows:
        wf = r["workflow_id"]
        cfg = db.execute("SELECT config FROM configs WHERE workflow_id=? AND version=?", (wf, r["version"])).fetchone()
        share = ""
        if cfg:
            c = json.loads(cfg["config"])
            al = (c["allocations"].get(r["cohort"]) or {})
            wm = (al.get("welcome_message") or c["allocations"]["default"]["welcome_message"]).get(r["wm"])
            vo = (al.get("voice") or c["allocations"]["default"]["voice"]).get(r["vo"])
            share = f" (that cohort's allocation then: {r['wm']} {wm:.0%}, {r['vo']} {vo:.0%})" if wm and vo else ""
        ch = change_record(db, wf, r["version"]) if r["version"] > 1 else {"who": "business default (v1)"}
        L.append(f"- {label(r['minute'])}  {r['lead_id']}  welcome={r['wm']} voice={r['vo']} caller_id={r['did']} "
                 f"prompt={r['prompt']}  cohort={r['cohort']}  config v{r['version']}{share}  "
                 f"engaged={'yes' if r['engaged'] else 'no'}")
        p = ch.get("proposal") or {}
        L.append(f"    why v{r['version']} was live: {ch.get('who')}"
                 + (f" — {p.get('change_summary')}" if p else ""))
    return "\n".join(L)
