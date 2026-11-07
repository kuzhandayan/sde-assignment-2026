"""Caller-ID health (C5): detect a degraded number, pull it, spread load, explore new numbers safely.

Caller ID is drawn independently per dial from the cohort's distribution, so within any time window every
number sees the same mix of people and hours: comparing a number's pickup with the pooled pickup of the other
numbers over the same window is a fair comparison with no modelling needed.

States: unknown -> probing -> healthy | bad.   healthy -> bad when it degrades.
- unknown numbers get a small probe share (5% each, 15% max) until they have DID_PROBE_MIN_DIALS dials;
- healthy numbers split the rest EQUALLY: spam-flagging and carrier reputation scale with per-number volume,
  so the least-loaded allocation is the safest one;
- a number whose pickup ratio vs the others is < 0.80 with z < -3 in any rolling window (3h/6h/24h) is pulled;
- a pulled number rests 48h and is then re-probed: degradation from heavy use recovers, a real spam flag
  fails the probe again at a cost of 5% of traffic for about a day.
"""
from __future__ import annotations

import json

from .. import settings as S
from ..stats import ratio_ci, z_two_prop


def _statuses(ctx, wf):
    return {d: (s, since, note) for d, s, since, note in
            ctx.store.q("SELECT did, status, since_minute, note FROM dids WHERE workflow_id=?", (wf,))}


def _set(ctx, wf, did, status, note):
    ctx.store.x("INSERT INTO dids VALUES (?,?,?,?,?) ON CONFLICT DO UPDATE SET status=excluded.status, "
                "since_minute=excluded.since_minute, note=excluded.note", (wf, did, status, ctx.now, note))


def bootstrap(ctx, wf: str) -> None:
    """Classify numbers from history: used ones are measured, never-used ones are 'unknown'."""
    opts = ctx.wfs[wf]["options"]["caller_id"]
    hist = ctx.ev.pickup_by_did(wf, -400 * 1440, 0)
    for did in opts:
        n, c = hist.get(did, (0, 0))
        if n < 500:
            _set(ctx, wf, did, "unknown", f"{n} history dials")
            continue
        on = sum(v[0] for k, v in hist.items() if k != did)
        oc = sum(v[1] for k, v in hist.items() if k != did)
        r, lo, hi = ratio_ci(c, n, oc, on)
        z = z_two_prop(c, n, oc, on)
        bad = on > 0 and r < S.DID_BAD_RATIO and z < S.DID_BAD_Z
        _set(ctx, wf, did, "bad" if bad else "healthy",
             f"history: pickup {c / n:.3f} on {n} dials, ratio vs others {r:.2f} [{lo:.2f},{hi:.2f}]")
    ctx.store.decide(ctx.now, wf, "callerid.bootstrap", "caller-ID status from history: " + ", ".join(
        f"{d}={s[0]}" for d, s in sorted(_statuses(ctx, wf).items())), {d: s for d, s in _statuses(ctx, wf).items()})


def review(ctx, wf: str, live_dist: dict) -> dict:
    """Update statuses from recent data. Returns {"target": dist, "urgent": bool, "why": [...], "evidence": {}}."""
    st = _statuses(ctx, wf)
    opts = ctx.wfs[wf]["options"]["caller_id"]
    why, urgent, evidence = [], False, {}
    in_use = [d for d, w in live_dist.items() if w > 0]
    for did in in_use:
        status = st.get(did, ("unknown", None, ""))[0]
        if status == "bad":
            continue
        for hrs in S.DID_WINDOWS_H:
            win = ctx.ev.pickup_by_did(wf, ctx.now - hrs * 60, ctx.now)
            n, c = win.get(did, (0, 0))
            on = sum(v[0] for k, v in win.items() if k != did)
            oc = sum(v[1] for k, v in win.items() if k != did)
            if n < S.DID_MIN_WINDOW_DIALS or on < S.DID_MIN_WINDOW_DIALS:
                continue
            r, lo, hi = ratio_ci(c, n, oc, on)
            z = z_two_prop(c, n, oc, on)
            evidence[f"{did}@{hrs}h"] = {"dials": n, "pickup": round(c / n, 4), "others_pickup": round(oc / on, 4),
                                         "ratio": round(r, 3), "ci": [round(lo, 3), round(hi, 3)], "z": round(z, 2)}
            if r < S.DID_BAD_RATIO and z < S.DID_BAD_Z:
                ctx.store.set_meta(f"did_fails:{wf}:{did}", int(ctx.store.get_meta(f"did_fails:{wf}:{did}", 0)) + 1)
                _set(ctx, wf, did, "bad", f"{hrs}h window: pickup {c / n:.3f} vs {oc / on:.3f} (ratio {r:.2f}, "
                                          f"z {z:.1f}) over {n} dials")
                why.append(f"pull {did}: pickup {c / n:.1%} vs {oc / on:.1%} on the other numbers over the last "
                           f"{hrs}h ({n} dials, z={z:.1f})")
                urgent = True
                ctx.store.decide(ctx.now, wf, "callerid.degraded", why[-1], evidence[f"{did}@{hrs}h"])
                break
            if status == "probing" and hrs == max(S.DID_WINDOWS_H):
                since = st[did][1] or 0
                tot = ctx.ev.pickup_by_did(wf, since, ctx.now)
                tn, tc = tot.get(did, (0, 0))
                ton = sum(v[0] for k, v in tot.items() if k != did)
                toc = sum(v[1] for k, v in tot.items() if k != did)
                if tn >= S.DID_PROBE_MIN_DIALS:
                    r2, lo2, _ = ratio_ci(tc, tn, toc, ton)
                    if lo2 >= S.DID_HEALTHY_RATIO_LB:
                        _set(ctx, wf, did, "healthy", f"probe passed: ratio {r2:.2f} (lower bound {lo2:.2f}) on {tn}")
                        why.append(f"promote {did} after probe: pickup ratio {r2:.2f} vs other numbers "
                                   f"(95% lower bound {lo2:.2f}, {tn} dials)")
                        ctx.store.decide(ctx.now, wf, "callerid.probe_passed", why[-1], {"ratio": r2, "lb": lo2})
                    elif tn >= 3 * S.DID_PROBE_MIN_DIALS and r2 < 0.9:
                        ctx.store.set_meta(f"did_fails:{wf}:{did}",
                                           int(ctx.store.get_meta(f"did_fails:{wf}:{did}", 0)) + 1)
                        _set(ctx, wf, did, "bad", f"probe failed: ratio {r2:.2f} on {tn} dials")
                        why.append(f"drop {did}: probe pickup ratio {r2:.2f} on {tn} dials")
                        ctx.store.decide(ctx.now, wf, "callerid.probe_failed", why[-1], {"ratio": r2})
    for d, (status, since, note) in _statuses(ctx, wf).items():
        fails = int(ctx.store.get_meta(f"did_fails:{wf}:{d}", 0))
        rest = S.DID_REST_HOURS * (2 ** max(fails - 1, 0))      # 48h, 96h, 192h ... after each failure
        if status == "bad" and since is not None and ctx.now - since >= rest * 60 and d not in in_use:
            _set(ctx, wf, d, "unknown", f"rested {rest}h after: {note}")
            ctx.store.decide(ctx.now, wf, "callerid.rest_over", f"{d} rested {rest}h (failure #{fails}); will "
                                                                f"re-probe at {S.DID_REPROBE_SHARE:.0%}", None)
    st = _statuses(ctx, wf)
    healthy = [d for d in opts if st.get(d, ("unknown",))[0] == "healthy"]
    probing = [d for d in opts if st.get(d, ("unknown",))[0] == "probing"]
    unknown = [d for d in opts if st.get(d, ("unknown",))[0] == "unknown"]
    if not healthy:   # nothing proven good: keep what's live minus anything bad
        keep = [d for d in in_use if st.get(d, ("unknown",))[0] != "bad"] or in_use
        return {"target": {d: 1 / len(keep) for d in keep}, "urgent": urgent, "why": why, "evidence": evidence}
    # start probing unknown numbers (only once we have a healthy base to fall back on)
    for d in unknown:
        if len(probing) * S.DID_PROBE_SHARE + S.DID_PROBE_SHARE <= S.DID_PROBE_MAX_TOTAL + 1e-9:
            _set(ctx, wf, d, "probing", "never used before: measuring on a small share")
            probing.append(d)
            why.append(f"probe {d} at {S.DID_PROBE_SHARE:.0%} (never used on this workflow, no evidence)")
    share = {d: (S.DID_REPROBE_SHARE if int(ctx.store.get_meta(f"did_fails:{wf}:{d}", 0)) else S.DID_PROBE_SHARE)
             for d in probing}
    probe_total = sum(share.values())
    target = dict(share)
    for d in healthy:
        target[d] = (1 - probe_total) / len(healthy)
    return {"target": target, "urgent": urgent, "why": why, "evidence": evidence}


def summary(ctx, wf: str) -> dict:
    return {d: {"status": s, "since": since, "note": note} for d, (s, since, note) in _statuses(ctx, wf).items()}
