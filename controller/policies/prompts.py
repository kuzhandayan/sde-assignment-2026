"""Hallucination incident response (C8): detect -> pick fix -> validate -> propose with evidence -> verify."""
from __future__ import annotations

import json

from .. import settings as S
from ..stats import binom_upper_p, wilson, z_two_prop


def baseline(ctx, wf: str) -> float:
    b = ctx.store.get_meta(f"hal_baseline:{wf}")
    if b is None:
        c, f, _ = ctx.ev.engagement(wf, -400 * 1440, 0)
        b = (f / c) if c >= 500 else 0.015
        b = max(b, 0.002)
        ctx.store.set_meta(f"hal_baseline:{wf}", b)
        ctx.store.decide(ctx.now, wf, "prompt.baseline", f"hallucination-flag baseline {b:.2%} from {c} "
                                                          f"connected history calls", {"flags": f, "connected": c})
    return b


def open_incident(ctx, wf: str):
    r = ctx.store.q("SELECT incident_id, detail FROM incidents WHERE workflow_id=? AND kind='hallucination' AND "
                    "status='open' ORDER BY opened_minute DESC LIMIT 1", (wf,))
    return (r[0][0], json.loads(r[0][1])) if r else (None, None)


def _save(ctx, iid, d):
    ctx.store.x("UPDATE incidents SET detail=? WHERE incident_id=?", (json.dumps(d), iid))


def _close(ctx, iid, d, why):
    d["closed_reason"] = why
    ctx.store.x("UPDATE incidents SET status='closed', closed_minute=?, detail=? WHERE incident_id=?",
                (ctx.now, json.dumps(d), iid))


def detect(ctx, wf: str, live_prompt: str) -> dict | None:
    """Two windows: the last 4h, and everything since the live prompt went live (a known change point, capped at..."""
    b = baseline(ctx, wf)
    since = ctx.prompt_since(wf)
    windows = [max(ctx.now - S.HAL_WINDOW_MIN, since)]
    if since > ctx.now - 1440:
        windows.append(since)
    for lo in windows:
        c, f, e = ctx.ev.engagement(wf, lo, ctx.now, live_prompt)
        if c < S.HAL_MIN_CONNECTED:
            continue
        rate = f / c
        p = binom_upper_p(f, c, b)
        if rate > max(S.HAL_RATE_MULT * b, b + S.HAL_RATE_ABS) and p < S.HAL_P:
            return {"prompt": live_prompt, "connected": c, "flags": f, "rate": round(rate, 4),
                    "baseline": round(b, 4), "p_value": p, "window_from": lo,
                    "window": "since prompt change" if lo == since else f"last {S.HAL_WINDOW_MIN // 60}h"}
    return None


def known_good(ctx, wf: str, bad: str, options: list[str]) -> list[dict]:
    """Prompts this workflow has run with a near-baseline flag rate, most recently live first."""
    b = baseline(ctx, wf)
    stats = ctx.ev.qa_by_prompt(wf, -400 * 1440, ctx.now)
    order = [r[0] for r in ctx.store.q("SELECT json_extract(config, '$.prompt_version') FROM configs "
                                       "WHERE workflow_id=? ORDER BY version DESC", (wf,))]
    out = []
    for pv, (c, f, e) in stats.items():
        if pv == bad or pv not in options or c < S.HAL_KNOWN_GOOD_MIN_CONNECTED:
            continue
        lo, hi = wilson(f, c)
        if f / c <= 1.3 * b and hi <= 2 * b:
            out.append({"prompt": pv, "connected": c, "flag_rate": round(f / c, 4), "engagement": round(e / c, 4),
                        "recency": order.index(pv) if pv in order else 99})
    return sorted(out, key=lambda x: x["recency"])


def step(ctx, wf: str, live_cfg: dict, options: list[str], policy_min: float) -> dict | None:
    """Advance the incident state machine one step. Returns a prompt change to propose, or None."""
    live_prompt = live_cfg["prompt_version"]
    iid, d = open_incident(ctx, wf)
    if iid is None:
        hit = detect(ctx, wf, live_prompt)
        if not hit:
            return None
        iid = f"inc:{wf}:hal:{ctx.now}"
        d = {"phase": "detected", "bad_prompt": live_prompt, "detection": hit, "candidates": [], "validations": [],
             "proposals": []}
        ctx.store.x("INSERT OR IGNORE INTO incidents VALUES (?,?,?,?,?,?,?)",
                    (iid, wf, "hallucination", "open", ctx.now, None, json.dumps(d)))
        ctx.store.decide(ctx.now, wf, "incident.opened",
                         f"hallucination flags {hit['rate']:.1%} on {live_prompt} over {hit['connected']} connected "
                         f"calls vs baseline {hit['baseline']:.1%} (p={hit['p_value']:.1e})", hit)
        ctx.store.alert(ctx.now, "page", wf, f"{wf}: hallucination spike on prompt {live_prompt}",
                        f"controller is preparing a validated rollback; check approvals for {wf}")
    # the bad prompt was replaced by someone else (supervisor) or by us
    if d["phase"] in ("detected", "validated", "proposed") and live_prompt != d["bad_prompt"]:
        d["phase"] = "verifying"
        d["fix_prompt"] = live_prompt
        d["fix_applied_minute"] = ctx.now
        d.setdefault("pre_incident_prompt", d.get("candidate"))
        ctx.store.decide(ctx.now, wf, "incident.fix_live", f"prompt is now {live_prompt}; verifying on live "
                                                           f"traffic", {"incident": iid})
    if d["phase"] == "detected":
        cand = known_good(ctx, wf, d["bad_prompt"], options)
        d["candidates"] = cand
        if not cand and ctx.credits() >= 3 + S.VALIDATION_N / 100:
            r = ctx.api.suggest_fixes(wf, f"hallucination flag rate {d['detection']['rate']:.1%} on prompt "
                                          f"{d['bad_prompt']} (baseline {d['detection']['baseline']:.1%})")
            if r.ok:
                d["llm"] = r.body["suggestions"]
                d["candidates"] = [{"prompt": s["prompt_version"], "summary": s["summary"], "source": "llm"}
                                   for s in r.body["suggestions"]][:2]
                ctx.store.decide(ctx.now, wf, "incident.llm_suggestions", "LLM suggested: " + ", ".join(
                    s["prompt_version"] for s in r.body["suggestions"]), r.body)
        for c in d["candidates"]:
            if any(v["prompt"] == c["prompt"] for v in d["validations"]):
                continue
            if ctx.credits() < S.VALIDATION_N / 100:
                ctx.store.alert(ctx.now, "page", wf, f"{wf}: out of credits during hallucination incident",
                                "top up credits; the fix cannot be validated")
                break
            r = ctx.api.validate(wf, c["prompt"], S.VALIDATION_N)
            if not r.ok:
                continue
            v = {k: r.body[k] for k in ("validation_run_id", "prompt_version", "n", "failures", "pass_rate")}
            v["prompt"] = c["prompt"]
            v["wilson_lb"] = round(wilson(r.body["n"] - r.body["failures"], r.body["n"])[0], 4)
            d["validations"].append(v)
            ok = v["pass_rate"] >= policy_min + S.VALIDATION_MARGIN
            ctx.store.decide(ctx.now, wf, "incident.validation",
                             f"validated {c['prompt']}: pass rate {v['pass_rate']:.3f} on n={v['n']} "
                             f"({'meets' if ok else 'below'} our bar {policy_min + S.VALIDATION_MARGIN:.3f})", v)
            if ok:
                d["phase"] = "validated"
                d["candidate"] = c["prompt"]
                d["validation_run_id"] = v["validation_run_id"]
                d["candidate_info"] = c
                break
        if d["phase"] == "detected":
            d["phase"] = "no_fix"
            ctx.store.alert(ctx.now, "page", wf, f"{wf}: no validated fix for hallucination spike",
                            "a human needs to pick a prompt; validation results are in the incident record")
        _save(ctx, iid, d)
    if d["phase"] in ("validated", "proposed"):
        _save(ctx, iid, d)
        det = d["detection"]
        cand = d.get("candidate_info") or {}
        sev = min(det["rate"] / max(det["baseline"], 1e-3) / 10, 0.4)
        return {
            "incident_id": iid, "prompt": d["candidate"], "validation_run_id": d["validation_run_id"],
            "summary": f"Roll back prompt {d['bad_prompt']} -> {d['candidate']}: hallucination flags at "
                       f"{det['rate']:.1%} vs {det['baseline']:.1%} normal",
            "rationale": (f"Since {d['bad_prompt']} went live, {det['flags']} of {det['connected']} connected calls "
                          f"were flagged for hallucination ({det['rate']:.1%}; normal is {det['baseline']:.1%}; "
                          f"p={det['p_value']:.1e}). {d['candidate']} "
                          + (f"ran on {cand['connected']} connected calls here with a {cand['flag_rate']:.1%} flag "
                             f"rate and {cand['engagement']:.1%} engagement" if cand.get("connected") else
                             f"was suggested by the LLM: {cand.get('summary', '')}")
                          + f"; validation {d['validation_run_id']} passed."),
            "impact": round(0.6 + sev, 3),
            "detection": det, "candidate": cand,
            "validation": next(v for v in d["validations"] if v["validation_run_id"] == d["validation_run_id"]),
        }
    if d["phase"] == "verifying":
        c, f, e = ctx.ev.engagement(wf, d["fix_applied_minute"] + S.STEP_MINUTES, ctx.now, live_prompt)
        b = baseline(ctx, wf)
        if c >= S.HAL_VERIFY_MIN_CONNECTED:
            rate = f / c
            ok = rate <= S.HAL_RESOLVED_MULT * b or binom_upper_p(f, c, b) > 0.01
            pre = d.get("pre_incident_engagement")
            if pre is None:
                pc, _, pe = ctx.ev.engagement(wf, d["detection"]["window_from"] - 3 * 1440,
                                              d["detection"]["window_from"], live_prompt)
                pre = [pc, pe]
                d["pre_incident_engagement"] = pre
            eng_drop = None
            if pre[0] >= 300:
                z = z_two_prop(pre[1], pre[0], e, c)
                eng_drop = {"before": round(pre[1] / pre[0], 4), "after": round(e / c, 4), "z": round(z, 2)}
            d["verification"] = {"connected": c, "flags": f, "rate": round(rate, 4), "engagement": eng_drop}
            if ok:
                ctx.store.decide(ctx.now, wf, "incident.verified",
                                 f"fix verified: flags {rate:.1%} on {c} connected calls with {live_prompt} "
                                 f"(baseline {b:.1%})", d["verification"])
                if eng_drop and eng_drop["z"] > 2.58 and eng_drop["after"] < eng_drop["before"] * 0.95:
                    ctx.store.alert(ctx.now, "ticket", wf, f"{wf}: engagement lower after prompt fix",
                                    f"engagement {eng_drop['before']:.1%} -> {eng_drop['after']:.1%} on "
                                    f"{live_prompt}; review whether another validated prompt is better")
                _close(ctx, iid, d, "verified")
                return None
            if c >= 3 * S.HAL_VERIFY_MIN_CONNECTED:
                ctx.store.alert(ctx.now, "page", wf, f"{wf}: hallucinations still high after fix",
                                f"flags {rate:.1%} on {live_prompt}; incident {iid}")
                _close(ctx, iid, d, "fix_did_not_work")
                return None
        _save(ctx, iid, d)
    return None


def mark_proposed(ctx, wf: str, proposal_id: str) -> None:
    iid, d = open_incident(ctx, wf)
    if iid:
        d["phase"] = "proposed"
        d["proposals"].append(proposal_id)
        _save(ctx, iid, d)
