"""Consolidated supervisor view (C11) and loop health (C14)."""
from __future__ import annotations

import html
import json
import os
import sqlite3

from .simtime import label


def _db(path):
    db = sqlite3.connect(f"file:{path}?mode=ro", uri=True, check_same_thread=False)
    db.row_factory = sqlite3.Row
    return db


def snapshot(path: str, tenant: str | None = None) -> dict:
    db = _db(path)
    now = db.execute("SELECT COALESCE(MAX(minute),0) FROM metrics").fetchone()[0]
    # at exactly midnight (e.g. the run just ended) "today" has no calls yet: show the last full day
    today = now // 1440 - 1 if now % 1440 == 0 and now > 0 else now // 1440
    out = {"now": label(now), "tenants": {}}
    for w in db.execute("SELECT workflow_id, tenant_id, body FROM workflows ORDER BY workflow_id"):
        if tenant and w["tenant_id"] != tenant:
            continue
        wf = w["workflow_id"]
        info = json.loads(w["body"])
        cfg = db.execute("SELECT version, actor, config FROM configs WHERE workflow_id=? ORDER BY version DESC LIMIT 1",
                         (wf,)).fetchone()
        live = json.loads(cfg["config"]) if cfg else {}
        tests = []
        for e in db.execute("SELECT alloc_key, dim, state FROM experiments WHERE workflow_id=?", (wf,)):
            st = json.loads(e["state"])
            if st.get("status") == "idle":
                continue
            al = (live.get("allocations", {}).get(e["alloc_key"]) or {}).get(e["dim"]) or \
                live.get("allocations", {}).get("default", {}).get(e["dim"])
            tests.append({"cohort": e["alloc_key"], "dim": e["dim"], "status": st["status"], "winner": st.get("winner"),
                          "suspended": sorted(st.get("suspended", {})), "live_allocation": al,
                          "last_event": st["log"][-1][2] if st.get("log") else None})
        pending = [dict(r) for r in db.execute(
            "SELECT proposal_id, approval_id, status, purpose, submitted_minute, json_extract(body,'$.change_summary') "
            "summary, json_extract(body,'$.impact_score') impact, json_extract(body,'$.affected_leads') affected "
            "FROM proposals WHERE workflow_id=? AND channel='approval' AND status IN ('pending','approved','applying') "
            "ORDER BY impact DESC", (wf,))]
        changed = []
        for r in db.execute("SELECT minute, body FROM world_events WHERE workflow_id=? AND type='config_changed' AND "
                            "minute >= ? ORDER BY minute", (wf, today * 1440)):
            b = json.loads(r["body"])
            s = db.execute("SELECT json_extract(body,'$.change_summary') FROM proposals WHERE proposal_id=?",
                           (b.get("proposal_id"),)).fetchone() if b.get("proposal_id") else None
            changed.append({"at": label(r["minute"]), "version": b["version"], "actor": b["actor"],
                            "dims": b["changed_dims"], "summary": s[0] if s else
                            ("supervisor edit" if b["actor"] == "supervisor" else None)})
        dids = {r["did"]: r["status"] for r in db.execute("SELECT did, status FROM dids WHERE workflow_id=?", (wf,))}
        inc = [dict(r) for r in db.execute("SELECT incident_id, kind, status, opened_minute, closed_minute FROM incidents WHERE "
                                           "workflow_id=? ORDER BY opened_minute DESC LIMIT 3", (wf,))]
        cohorts = [dict(r) for r in db.execute("SELECT cohort_id, purpose, reason FROM cohorts WHERE workflow_id=? "
                                               "AND status='active' ORDER BY purpose DESC, cohort_id", (wf,))]
        # supervisor edits still on hold: not superseded by a later approved change on the same dim
        approved = [(r[0], json.loads(r[1])) for r in db.execute(
            "SELECT minute, body FROM world_events WHERE workflow_id=? AND type='config_changed' AND "
            "json_extract(body,'$.actor')='controller_approved'", (wf,))]
        frozen = [dict(r) for r in db.execute("SELECT dim, until_minute, reason, until_minute - 1440 AS edited "
                                              "FROM frozen_dims WHERE workflow_id=?",
                                              (wf,))]
        frozen = [f for f in frozen if not any(m >= f["edited"] and f["dim"] in b.get("changed_dims", [])
                                               for m, b in approved)]
        k_today = _k(db, wf, today * 1440, (today + 1) * 1440)
        k_base = _k(db, wf, -14 * 1440, 0)
        out["tenants"].setdefault(w["tenant_id"], {})[wf] = {
            "use_case": info.get("use_case"), "objective": info["objective"],
            "config_version": cfg["version"] if cfg else None, "prompt": live.get("prompt_version"),
            "day": f"D{today}", "kpis_today": k_today, "kpis_before_controller": k_base,
            "being_tested": tests, "wanted_from_you": pending, "changed_today": changed, "caller_ids": dids,
            "incidents": inc, "cohorts": cohorts, "supervisor_edits_respected": frozen}
    out["alerts"] = [dict(r) for r in db.execute("SELECT minute, severity, workflow_id, summary, action FROM alerts "
                                                  "ORDER BY id DESC LIMIT 20")]
    return out


def _k(db, wf, lo, hi):
    p = db.execute("SELECT COALESCE(SUM(dials),0), COALESCE(SUM(conn),0) FROM agg_pick WHERE workflow_id=? AND "
                   "day*1440+hour*60 >= ? AND day*1440+hour*60 < ?", (wf, lo, hi)).fetchone()
    e = db.execute("SELECT COALESCE(SUM(conn),0), COALESCE(SUM(eng),0) FROM agg_qa WHERE workflow_id=? AND slot>=? "
                   "AND slot<?", (wf, lo // 30, hi // 30)).fetchone()
    return {"pickup_rate": round(p[1] / p[0], 4) if p[0] else None,
            "engagement_rate": round(e[1] / e[0], 4) if e[0] else None, "dials": p[0]}


def loop_health(path: str) -> dict:
    db = _db(path)
    now = db.execute("SELECT COALESCE(MAX(minute),0) FROM metrics").fetchone()[0]

    def series(name, since):
        return [r[0] for r in db.execute("SELECT value FROM metrics WHERE name=? AND minute>? ORDER BY minute",
                                         (name, since))]
    ev = series("ingest_events", now - 1440)
    wall = series("ingest_wall_s", now - 1440)
    lag = series("decision_lag_s", now - 1440)
    cr = series("credits_remaining", -10 ** 9)
    return {"now": label(now),
            "ingest_events_last_sim_day": int(sum(ev)),
            "ingest_events_per_wall_s": round(sum(ev) / sum(wall), 0) if sum(wall) else None,
            "decision_lag_s_p50": sorted(lag)[len(lag) // 2] if lag else None,
            "decision_lag_s_max": max(lag) if lag else None,
            "decisions_last_sim_hour": db.execute("SELECT COUNT(*) FROM decisions WHERE minute > ?",
                                                  (now - 60,)).fetchone()[0],
            "credits_remaining": cr[-1] if cr else None, "credits_used": (cr[0] - cr[-1]) if cr else None,
            "peak_rss_mb": max(series("rss_mb", -10 ** 9) or [0]),
            "pending_approvals": db.execute("SELECT COUNT(*) FROM proposals WHERE status IN ('pending','approved',"
                                            "'applying')").fetchone()[0],
            "chunks_ingested": db.execute("SELECT COUNT(*) FROM chunks_done").fetchone()[0],
            "alerts_page": [dict(r) for r in db.execute("SELECT minute, workflow_id, summary, action FROM alerts "
                                                         "WHERE severity='page' ORDER BY id DESC LIMIT 10")]}


# ------------------------------------------------------------------------------------------------ rendering
def _h(x):
    return html.escape(str(x)) if x is not None else ""


def _dist(d):
    return ", ".join(f"{k} {v:.0%}" for k, v in sorted((d or {}).items()))


def render_tenant(snap: dict, tenant: str) -> str:
    wfs = snap["tenants"].get(tenant, {})
    P = [f"<html><head><meta charset='utf-8'><title>{_h(tenant)} — what the agent is doing</title><style>"
         "body{font-family:system-ui,sans-serif;max-width:1100px;margin:24px auto;color:#222}"
         "h2{border-bottom:2px solid #ddd;padding-bottom:4px} table{border-collapse:collapse;width:100%;margin:6px 0}"
         "td,th{border:1px solid #e3e3e3;padding:5px 8px;text-align:left;font-size:14px;vertical-align:top}"
         "th{background:#f6f6f6}.pill{padding:1px 8px;border-radius:10px;background:#eef}.bad{background:#fdd}"
         ".ok{background:#dfd}</style></head><body>",
         f"<h1>{_h(tenant)}</h1><p>As of <b>{_h(snap['now'])}</b> (simulated). Pickup and engagement are shown "
         f"separately and never blended.</p>"]
    for wf, d in wfs.items():
        kt, kb = d["kpis_today"], d["kpis_before_controller"]
        P.append(f"<h2>{_h(wf)} <small>— {_h(d['use_case'])}</small></h2>"
                 f"<p>Primary KPI <b>{_h(d['objective']['primary'])}</b>, guardrail {_h(d['objective']['guardrail'])}"
                 f" · config v{_h(d['config_version'])} · prompt {_h(d['prompt'])}</p>"
                 f"<table><tr><th></th><th>pickup</th><th>engagement</th></tr>"
                 f"<tr><td>{_h(d['day'])} (latest day)</td><td>{_h(kt['pickup_rate'])}</td><td>{_h(kt['engagement_rate'])}</td></tr>"
                 f"<tr><td>before the controller (history)</td><td>{_h(kb['pickup_rate'])}</td>"
                 f"<td>{_h(kb['engagement_rate'])}</td></tr></table>")
        P.append("<h3>What we want from you</h3>")
        if d["wanted_from_you"]:
            P.append("<table><tr><th>request</th><th>impact</th><th>affected leads</th><th>status</th></tr>" + "".join(
                f"<tr><td>{_h(p['summary'])}</td><td>{_h(p['impact'])}</td><td>{_h(p['affected'])}</td>"
                f"<td>{_h(p['status'])} ({_h(p['approval_id'])})</td></tr>" for p in d["wanted_from_you"]) + "</table>")
        else:
            P.append("<p>Nothing waiting for you.</p>")
        P.append("<h3>Being tested / what's winning</h3><table><tr><th>cohort</th><th>dimension</th><th>status</th>"
                 "<th>live split</th><th>latest</th></tr>" + "".join(
                     f"<tr><td>{_h(t['cohort'])}</td><td>{_h(t['dim'])}</td><td><span class='pill "
                     f"{'ok' if t['status'] == 'promoted' else ''}'>{_h(t['status'])}"
                     f"{(' — ' + _h(t['winner'])) if t['winner'] else ''}</span></td>"
                     f"<td>{_h(_dist(t['live_allocation']))}</td><td>{_h(t['last_event'])}</td></tr>"
                     for t in d["being_tested"]) + "</table>")
        P.append(f"<h3>What changed on {_h(d['day'])}</h3>")
        P.append("<table><tr><th>when</th><th>version</th><th>by</th><th>what</th></tr>" + "".join(
            f"<tr><td>{_h(c['at'])}</td><td>v{_h(c['version'])}</td><td>{_h(c['actor'])}</td>"
            f"<td>{_h(c['summary'] or ', '.join(c['dims']))}</td></tr>" for c in d["changed_today"]) + "</table>"
                 if d["changed_today"] else f"<p>No changes on {_h(d['day'])}.</p>")
        P.append("<h3>Caller IDs</h3><p>" + " ".join(
            f"<span class='pill {'bad' if s == 'bad' else 'ok' if s == 'healthy' else ''}'>{_h(k)}: {_h(s)}</span>"
            for k, s in sorted(d["caller_ids"].items())) + "</p>")
        if d["supervisor_edits_respected"]:
            P.append("<p><b>Your edits we are leaving alone:</b> " + "; ".join(
                f"{_h(f['dim'])} ({_h(f['reason'])})" for f in d["supervisor_edits_respected"]) + "</p>")
        if d["incidents"]:
            P.append("<p><b>Incidents:</b> " + "; ".join(
                f"{_h(i['kind'])}: opened {_h(label(i['opened_minute']))}, "
                + (f"resolved {_h(label(i['closed_minute']))}" if i["closed_minute"] is not None else "still open")
                for i in d["incidents"])
                     + "</p>")
    P.append("</body></html>")
    return "".join(P)


def markdown_report(path: str) -> str:
    snap = snapshot(path)
    h = loop_health(path)
    L = [f"# Supervisor view snapshot — {snap['now']}", "", "## Loop health", "", "```json",
         json.dumps(h, indent=2, default=str), "```"]
    for tenant, wfs in snap["tenants"].items():
        L += ["", f"## {tenant}"]
        for wf, d in wfs.items():
            L += ["", f"### {wf} — primary {d['objective']['primary']}, config v{d['config_version']}, prompt "
                      f"{d['prompt']}", "",
                  f"- KPIs today: {d['kpis_today']} · before controller: {d['kpis_before_controller']}",
                  f"- Caller IDs: {d['caller_ids']}",
                  f"- Cohorts: " + ", ".join(c["cohort_id"] for c in d["cohorts"]), "", "| cohort | dim | status | live split |",
                  "|---|---|---|---|"]
            L += [f"| {t['cohort']} | {t['dim']} | {t['status']}{(' — ' + t['winner']) if t['winner'] else ''} | "
                  f"{_dist(t['live_allocation'])} |" for t in d["being_tested"]]
            if d["wanted_from_you"]:
                L += ["", "Waiting for approval:"] + [f"- {p['summary']} (impact {p['impact']}, {p['affected']} "
                                                       f"leads)" for p in d["wanted_from_you"]]
    return "\n".join(L)


def serve(path: str, host: str = "127.0.0.1", port: int = 8800) -> None:
    from fastapi import FastAPI, HTTPException, Request
    from fastapi.responses import HTMLResponse, PlainTextResponse
    import uvicorn
    from .audit import why

    app = FastAPI(title="Formi controller — supervisor view")
    token = os.environ.get("VIEW_TOKEN")

    @app.middleware("http")
    async def auth(request: Request, call_next):
        if token and request.headers.get("authorization") != f"Bearer {token}":
            return PlainTextResponse("unauthorised", status_code=401)
        return await call_next(request)

    @app.get("/", response_class=HTMLResponse)
    def index():
        s = snapshot(path)
        return "<h1>Tenants</h1><ul>" + "".join(f"<li><a href='/tenant/{_h(t)}'>{_h(t)}</a></li>"
                                                for t in s["tenants"]) + "</ul><p><a href='/api/loop'>loop health</a></p>"

    @app.get("/tenant/{tenant}", response_class=HTMLResponse)
    def tenant_page(tenant: str):
        s = snapshot(path, tenant)
        if tenant not in s["tenants"]:
            raise HTTPException(404, "unknown tenant")
        return render_tenant(s, tenant)

    @app.get("/api/tenant/{tenant}")
    def tenant_json(tenant: str):
        return snapshot(path, tenant)

    @app.get("/api/loop")
    def loop():
        return loop_health(path)

    @app.get("/api/why", response_class=PlainTextResponse)
    def why_ep(workflow: str, at: str):
        return why(path, workflow, at)

    uvicorn.run(app, host=host, port=port, log_level="warning")
