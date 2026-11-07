"""Welcome-message x voice experimentation (C6), winner promotion, decay detection and rollback (C7).

Unit of experimentation: (allocation key, dim), where the allocation key is `default` or a variant-segment
cohort. welcome_message and voice are randomised independently per call, so the two dims form a factorial
design: each dim's arms are compared averaged over the other dim, at no extra traffic cost.

Per (key, dim), every review:
1. Evidence = post-stratified engagement per arm (data.arm_stats_from), discounted with a 1.5-day half-life so
   the estimate tracks the present (this is what makes decay visible).
2. Harm stop: an arm significantly worse than the best (one-sided z, alpha 0.01 Bonferroni over arms,
   n >= 150) is suspended (share 0). Suspended arms come back only when a rollback re-opens exploration, so
   a winner that decays can be replaced by an arm that was worse at the time.
3. Exploring: allocation follows P(best) (Beta posteriors, seeded Monte Carlo -> deterministic) with a 10% floor
   per live arm; the very first allocation keeps 50% on the business default.
4. Promotion: P(best) >= 0.95 AND n >= 300 AND Holm-corrected one-sided tests vs every other live arm at
   alpha 0.05. Winner gets 1 - floors; each other live arm keeps a 5% floor (15% total max) as a reference.
5. Decay: a promoted winner whose last-day rate is significantly below its rate at promotion (p < 0.01, >= 6%
   relative), when the reference arms did not fall the same way, or whose P(best) drops under 0.5, is rolled
   back to exploring.

Experiments run on every workflow. Welcome message and voice are heard after the call connects, so they move
engagement only: the primary KPI on engagement-primary workflows, the guardrail on pickup-primary ones (where
call-time gains push the engagement RATE down through mix, see schedule.engagement_guardrail). On
pickup-primary workflows the first exploration is gentler (70% stays on the business default).
"""
from __future__ import annotations

import json
import math
from collections import defaultdict

from .. import settings as S
from ..cohorts import cohort_of, dist, matches
from ..data import arm_stats_from
from ..ingest import FEATS
from ..stats import holm, norm_sf, normalise, prob_best, seed_of, z_two_prop

DIMS = ("welcome_message", "voice")


def _state(ctx, wf, key, dim) -> dict:
    v = ctx.store.q1("SELECT state FROM experiments WHERE workflow_id=? AND alloc_key=? AND dim=?", (wf, key, dim))
    return json.loads(v) if v else {"status": "idle", "suspended": {}, "log": []}


def _save(ctx, wf, key, dim, st):
    st["log"] = st.get("log", [])[-20:]
    ctx.store.x("INSERT INTO experiments VALUES (?,?,?,?,?) ON CONFLICT DO UPDATE SET state=excluded.state, "
                "updated_minute=excluded.updated_minute", (wf, key, dim, json.dumps(st), ctx.now))


def all_states(ctx, wf) -> dict:
    return {(k, d): json.loads(s) for k, d, s in
            ctx.store.q("SELECT alloc_key, dim, state FROM experiments WHERE workflow_id=?", (wf,))}


def population(ctx, wf: str, key: str, dim: str, segments: list[dict]) -> set:
    """Codes whose allocation for `dim` is governed by `key` (segments that set `dim` claim their members)."""
    owning = [s for s in segments if _state(ctx, wf, s["id"], dim)["status"] != "idle"]
    out = set()
    for cid in ctx.codes.by_id:
        f = ctx.codes.feats(cid)
        owner = next((s["id"] for s in owning if matches(s["where"], f)), "default")
        if owner == key:
            out.add(cid)
    return out


def _posteriors(arms, stats, alive):
    rates = [stats[a]["rate"] for a in alive if a in stats and stats[a]["rate"] is not None]
    mean = sum(rates) / len(rates) if rates else 0.5
    A, B = [], []
    for a in alive:
        s = stats.get(a)
        if s and s["rate"] is not None and s["n"] > 0:
            A.append(1 + s["rate"] * s["n"])
            B.append(1 + (1 - s["rate"]) * s["n"])
        else:
            A.append(1 + mean * 5)
            B.append(1 + (1 - mean) * 5)
    return A, B


def review_key(ctx, wf: str, key: str, dim: str, rows, codes: set, control: str, live: dict) -> dict:
    """One (key, dim) review. Returns {"target", "event", "why", "stats"}; updates the stored state."""
    arms = list(ctx.wfs[wf]["options"][dim])
    st = _state(ctx, wf, key, dim)
    today = ctx.now // 1440
    st.setdefault("suspended", {})
    if st.get("evidence_from_day") is not None:
        rows = [r for r in rows if r[0] >= st["evidence_from_day"]]
    stats = arm_stats_from(rows, dim, today, S.EXP_HALF_LIFE_DAYS, codes)
    alive = [a for a in arms if a not in st["suspended"]]
    out = {"event": None, "why": [], "stats": {a: {k: (round(v, 4) if isinstance(v, float) else v)
                                                   for k, v in s.items()} for a, s in stats.items()}}

    if st["status"] == "idle":
        others = [a for a in alive if a != control]
        if not others:
            return {**out, "target": None}
        share = S.EXP_START_CONTROL_SHARE if ctx.wfs[wf]["objective"]["primary"] == "engagement_rate" \
            else S.EXP_START_CONTROL_SHARE_GUARDRAIL
        t = {control: share}
        for a in others:
            t[a] = (1 - share) / len(others)
        st.update(status="exploring", control=control, started_minute=ctx.now)
        st["log"].append([ctx.now, "start", f"explore {', '.join(others)} against {control}"])
        _save(ctx, wf, key, dim, st)
        return {**out, "target": normalise(t), "event": "start",
                "why": [f"{key}/{dim}: start exploring {', '.join(others)} with {control} kept at "
                        f"{share:.0%} (no evidence on alternatives yet)"]}

    # ---- harm stop
    measured = [a for a in alive if a in stats and stats[a]["rate"] is not None]
    if len(measured) >= 2 and st["status"] == "exploring":
        best = max(measured, key=lambda a: stats[a]["rate"])
        m = max(len(measured) - 1, 1)
        for a in measured:
            if a == best or stats[a]["raw_n"] < S.EXP_DROP_MIN_N:
                continue
            z = z_two_prop(stats[best]["rate"] * stats[best]["n"], stats[best]["n"],
                           stats[a]["rate"] * stats[a]["n"], stats[a]["n"])
            if norm_sf(z) < S.EXP_DROP_ALPHA / m and len(alive) > 1:
                st["suspended"][a] = ctx.now
                alive.remove(a)
                msg = (f"{key}/{dim}: suspend {a} -- engagement {stats[a]['rate']:.1%} vs {best} "
                       f"{stats[best]['rate']:.1%} (z={z:.1f}, n={stats[a]['raw_n']:.0f})")
                out["why"].append(msg)
                st["log"].append([ctx.now, "drop", msg])
                ctx.store.decide(ctx.now, wf, "experiment.drop", msg, {"key": key, "dim": dim, "stats": out["stats"]})
                if st.get("winner") == a:
                    st["status"], st["winner"] = "exploring", None
    if len(alive) == 1 and st["status"] == "exploring":
        w = alive[0]
        s_w = stats.get(w) or {}
        st.update(status="promoted", winner=w, promoted_minute=ctx.now, winner_rate=s_w.get("rate"),
                  winner_n=s_w.get("n", 0), ref_rate=None)
        msg = f"{key}/{dim}: {w} is the only arm not suspended -- promoted"
        st["log"].append([ctx.now, "promote", msg])
        ctx.store.decide(ctx.now, wf, "experiment.promote", msg, {"key": key, "dim": dim, "stats": out["stats"]})
        _save(ctx, wf, key, dim, st)
        return {**out, "target": {w: 1.0}, "event": "promote", "why": out["why"] + [msg]}

    A, B = _posteriors(arms, stats, alive)
    pb = prob_best(A, B, seed_of(wf, key, dim, today)) if len(alive) > 1 else [1.0]
    pbest = dict(zip(alive, pb))
    out["p_best"] = {a: round(p, 3) for a, p in pbest.items()}
    lead = max(alive, key=lambda a: pbest[a])

    if st["status"] == "promoted":
        w = st["winner"]
        decay = _decay(ctx, wf, key, dim, rows, codes, st, alive)
        if decay or pbest.get(w, 0) < 0.5:
            reason = decay or f"P(best) for {w} fell to {pbest.get(w, 0):.2f}"
            msg = f"{key}/{dim}: roll back winner {w} -- {reason}"
            revived = sorted(st["suspended"])
            st.update(status="exploring", winner=None, rolled_back_minute=ctx.now, suspended={},
                      evidence_from_day=today - 1, decayed=w)
            if revived:
                msg += f"; re-opening suspended arms {', '.join(revived)}"
                alive = [a for a in arms]
                for a in revived:
                    pbest[a] = 1.0 / len(arms)
            st["log"].append([ctx.now, "rollback", msg])
            ctx.store.decide(ctx.now, wf, "experiment.rollback", msg, {"key": key, "dim": dim, "p_best": pbest,
                                                                       "stats": out["stats"]})
            out["event"] = "rollback"
            out["why"].append(msg)
            t = _explore_target(alive, pbest, cap={w: 0.2})
            _save(ctx, wf, key, dim, st)
            return {**out, "target": t}
        _save(ctx, wf, key, dim, st)
        return {**out, "target": _promoted_target(w, alive)}

    # ---- exploring: promotion test
    s_lead = stats.get(lead)
    if s_lead and s_lead["raw_n"] >= S.EXP_MIN_ARM_N and pbest[lead] >= S.EXP_PROMOTE_PBEST:
        ps = []
        for a in alive:
            if a == lead:
                continue
            s = stats.get(a)
            if not s or s["rate"] is None:
                ps.append(1.0)
                continue
            z = z_two_prop(s_lead["rate"] * s_lead["n"], s_lead["n"], s["rate"] * s["n"], s["n"])
            ps.append(norm_sf(z))
        if all(holm(ps, S.EXP_ALPHA)):
            rate0 = s_lead["rate"]
            st.pop("decayed", None)
            st.update(status="promoted", winner=lead, promoted_minute=ctx.now, winner_rate=rate0,
                      winner_n=s_lead["n"],
                      ref_rate=_pooled([stats[a] for a in alive if a != lead and a in stats]))
            ref_arm = st.get("control", control)
            if ref_arm == lead or ref_arm not in stats:
                ref_arm = max((a for a in alive if a != lead and a in stats and stats[a]["rate"] is not None),
                              key=lambda a: stats[a]["rate"], default=None)
            ctl = stats.get(ref_arm) if ref_arm else None
            lift = (rate0 / ctl["rate"] - 1) if ctl and ctl.get("rate") else None
            msg = (f"{key}/{dim}: promote {lead} -- engagement {rate0:.1%}"
                   + (f" vs {ref_arm} {ctl['rate']:.1%} ({lift:+.1%})" if lift is not None else "")
                   + f", P(best)={pbest[lead]:.3f}, Holm p-values {[round(p, 4) for p in ps]}")
            st["log"].append([ctx.now, "promote", msg])
            ctx.store.decide(ctx.now, wf, "experiment.promote", msg, {"key": key, "dim": dim, "p_best": pbest,
                                                                      "stats": out["stats"]})
            _save(ctx, wf, key, dim, st)
            return {**out, "target": _promoted_target(lead, alive), "event": "promote", "why": out["why"] + [msg]}
    _save(ctx, wf, key, dim, st)
    t = _explore_target(alive, pbest)
    cur = dist(live, key, dim)
    # damping: move halfway toward the P(best) allocation, so posterior noise doesn't flip-flop the config
    t = normalise({a: 0.5 * cur.get(a, 0) + 0.5 * t.get(a, 0) for a in set(t) | set(cur) if a in alive})
    d = st.get("decayed")
    if d in t and t[d] > 0.2:
        # a winner that decayed stays capped until it earns promotion again on fresh evidence
        rest = sum(v for a, v in t.items() if a != d) or 1.0
        t = normalise({a: (0.2 if a == d else v * 0.8 / rest) for a, v in t.items()})
    return {**out, "target": t}


def _pooled(ss):
    n = sum(s["n"] for s in ss if s.get("rate") is not None)
    y = sum(s["rate"] * s["n"] for s in ss if s.get("rate") is not None)
    return y / n if n else None


def _explore_target(alive, pbest, cap=None, floor=0.10):
    t = {a: max(pbest.get(a, 0), 0) for a in alive}
    if cap:
        for a, c in cap.items():
            if a in t:
                t[a] = min(t[a], c)
    s = sum(t.values()) or 1.0
    t = {a: v / s for a, v in t.items()}
    k = len(alive)
    fl = min(floor, 1 / k)
    t = {a: fl + (1 - fl * k) * v for a, v in t.items()}
    return normalise(t)


def _promoted_target(w, alive):
    others = [a for a in alive if a != w]
    fl = min(S.EXP_FLOOR, 0.15 / max(len(others), 1)) if others else 0
    t = {a: fl for a in others}
    t[w] = 1 - fl * len(others)
    return normalise(t)


def _decay(ctx, wf, key, dim, rows, codes, st, alive) -> str | None:
    """Winner's last-day engagement vs its estimate at promotion, controlling for a global shift via the
    reference arms. Returns a reason string or None."""
    w = st["winner"]
    today = ctx.now // 1440
    if ctx.now - (st.get("promoted_minute") or ctx.now) < 1440 * S.EXP_DECAY_WINDOW_DAYS:
        return None
    if ctx.incident_open(wf):
        return None   # a prompt incident moves every arm; don't read it as decay
    recent = [r for r in rows if r[0] >= today - S.EXP_DECAY_WINDOW_DAYS]
    rs = arm_stats_from(recent, dim, today, 1e9, codes, contrast_only=False)
    s = rs.get(w)
    if not s or s["raw_n"] < 150 or not st.get("winner_rate"):
        return None
    # The rate at promotion is inflated by selection (winner's curse). Prefer the winner's rate measured AFTER
    # promotion (excluding the last day being tested); fall back to the promotion estimate shrunk halfway
    # toward the reference arms.
    pday = (st.get("promoted_minute") or 0) // 1440 + 1
    post = [r for r in rows if pday <= r[0] < today - S.EXP_DECAY_WINDOW_DAYS + 1]
    ps = arm_stats_from(post, dim, today, 1e9, codes, contrast_only=False).get(w)
    if ps and ps["raw_n"] >= 300:
        r0, n0 = ps["raw_y"] / ps["raw_n"], ps["raw_n"]
    else:
        r0 = st["winner_rate"]
        if st.get("ref_rate"):
            r0 = 0.5 * (r0 + st["ref_rate"]) if r0 > st["ref_rate"] else r0
        n0 = min(st.get("winner_n", 500), 2000)
    if not r0:
        return None
    z = z_two_prop(r0 * n0, n0, s["raw_y"], s["raw_n"])
    rel = 1 - (s["raw_y"] / s["raw_n"]) / r0
    ref_now = _pooled([dict(rate=rs[a]["raw_y"] / rs[a]["raw_n"], n=rs[a]["raw_n"])
                       for a in alive if a != w and a in rs and rs[a]["raw_n"] > 0])
    ref_rel = (1 - ref_now / st["ref_rate"]) if ref_now and st.get("ref_rate") else 0.0
    if norm_sf(z) < S.EXP_DECAY_ALPHA and rel - max(ref_rel, 0) >= S.EXP_DECAY_MIN_REL_DROP:
        return (f"last-day engagement {s['raw_y'] / s['raw_n']:.1%} vs {r0:.1%} at promotion "
                f"({-rel:+.1%}, z={z:.1f}, n={s['raw_n']:.0f}); reference arms moved {-ref_rel:+.1%}")
    return None


# ------------------------------------------------------------------------------------------- segments
def discover_segment(ctx, wf: str, rows, segments: list[dict], default_alloc: dict) -> dict | None:
    """Find one lead segment whose best arm differs significantly from the default population's preferred arm.
    Bonferroni over every (segment, dim) tested. Returns {"where", "dim", "arm", "z", "why"} or None."""
    if ctx.now // 1440 < S.SEG_START_DAY or len(segments) >= S.SEG_MAX:
        return None
    today = ctx.now // 1440
    tot_conn = sum(r[6] for r in rows) or 1
    # candidate segments: single feature values and feature pairs
    by_code = defaultdict(int)
    for r in rows:
        by_code[r[3]] += r[6]
    feats = {c: ctx.codes.feats(c) for c in by_code}
    cands = defaultdict(set)
    for c, f in feats.items():
        for i, a in enumerate(FEATS):
            cands[((a, f[a]),)].add(c)
            for b in FEATS[i + 1:]:
                cands[((a, f[a]), (b, f[b]))].add(c)
    existing = [s["where"] for s in segments]
    tests = []
    for seg, codes in cands.items():
        n = sum(by_code[c] for c in codes)
        if n < S.SEG_MIN_CONNECTED or n / tot_conn < S.SEG_MIN_SHARE:
            continue
        where = {a: [v] for a, v in seg}
        if any(_overlap(where, e, feats) > 0.5 for e in existing):
            continue
        for dim in DIMS:
            g = max(default_alloc[dim], key=default_alloc[dim].get)
            stt = arm_stats_from(rows, dim, today, S.EXP_HALF_LIFE_DAYS, codes)
            if g not in stt or stt[g]["rate"] is None:
                continue
            b = max((a for a in stt if stt[a]["rate"] is not None and stt[a]["raw_n"] >= 100),
                    key=lambda a: stt[a]["rate"], default=None)
            if b is None or b == g:
                tests.append(None)
                continue
            z = z_two_prop(stt[b]["rate"] * stt[b]["n"], stt[b]["n"], stt[g]["rate"] * stt[g]["n"], stt[g]["n"])
            # replication: the same direction must hold separately on even and on odd days
            halves = []
            for parity in (0, 1):
                hs = arm_stats_from([r for r in rows if r[0] % 2 == parity], dim, today, S.EXP_HALF_LIFE_DAYS, codes)
                if b in hs and g in hs and hs[b]["rate"] is not None and hs[g]["rate"] is not None:
                    halves.append(z_two_prop(hs[b]["rate"] * hs[b]["n"], hs[b]["n"],
                                             hs[g]["rate"] * hs[g]["n"], hs[g]["n"]))
                else:
                    halves.append(0.0)
            tests.append({"where": where, "dim": dim, "arm": b, "vs": g, "z": z, "n": n, "z_halves": halves,
                          "rate_b": stt[b]["rate"], "rate_g": stt[g]["rate"]})
    m = max(len(tests), 1)
    zcrit = _zcrit(S.SEG_ALPHA / m)
    sig = [t for t in tests if t and t["z"] > zcrit and min(t["z_halves"]) > 1.64]
    if not sig:
        return None
    t = max(sig, key=lambda t: t["z"])
    t["why"] = (f"segment {_fmt(t['where'])}: {t['dim']} {t['arm']} engages {t['rate_b']:.1%} vs {t['vs']} "
                f"{t['rate_g']:.1%} (z={t['z']:.1f} > {zcrit:.1f}, Bonferroni over {m} tests, n={t['n']}; replicated on "
                f"even/odd days z={t['z_halves'][0]:.1f}/{t['z_halves'][1]:.1f})")
    return t


def _zcrit(p):
    lo, hi = 0.0, 10.0
    for _ in range(60):
        mid = (lo + hi) / 2
        if norm_sf(mid) > p:
            lo = mid
        else:
            hi = mid
    return hi


def _overlap(a, b, feats) -> float:
    A = {c for c, f in feats.items() if matches(a, f)}
    B = {c for c, f in feats.items() if matches(b, f)}
    return len(A & B) / max(min(len(A), len(B)), 1)


def _fmt(where):
    return " & ".join(f"{k}={'|'.join(v)}" for k, v in where.items())


def expected_engagement(stats_by_dim: dict, alloc_by_dim: dict) -> float | None:
    """Relative engagement multiplier of an allocation, from per-arm rates (product across dims)."""
    tot = 1.0
    for dim, alloc in alloc_by_dim.items():
        st = stats_by_dim.get(dim) or {}
        rates = {a: s["rate"] for a, s in st.items() if s.get("rate") is not None}
        if not rates:
            continue
        base = sum(rates.values()) / len(rates)
        e = sum(w * rates.get(a, base) for a, w in alloc.items())
        tot *= e / base
    return tot
