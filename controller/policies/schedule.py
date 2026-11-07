"""Call-time optimisation (C3 + C4), per cohort.

The dialler always fills capacity; `hour_weights` only decide WHO it picks in each hour. So the lever is
comparative advantage: in hour h, prefer the people for whom h is a relatively good hour.

For cohort c:   q_c(h) = p_c(h) / (L_c * p_all(h))     (timing advantage, with the cohort's overall level L_c
                                                         divided out, so no cohort is called more overall)
                w_c(h) = clip(q_c(h) ** GAMMA, W_MIN, W_MAX)

p_c(h) is shrunk toward L_c * p_all(h) with SCHED_SHRINK_K pseudo-dials, so thin cells stay near flat.
Weights are never 0 (an hour where every eligible lead has weight 0 leaves capacity unused).

Which features define the cells is learned from history (C3): for each lead feature we test whether its values
have different hour profiles (chi-square excess over the degrees of freedom), and cross the two strongest.
Per-person hours were considered and rejected: a person has 2-3 dials of history, far too few to estimate a
personal hour curve (SUBMISSION.md section 5).
"""
from __future__ import annotations

import math
from collections import defaultdict

from .. import settings as S
from ..cohorts import cohort_of
from ..ingest import FEATS


def _hours(wfinfo) -> list[int]:
    lo, hi = wfinfo["dialling_window"]
    return list(range(lo, hi))


def discover_cells(ctx, wf: str) -> list[dict]:
    """Learn the call-time partition from history. Returns [{where, dials}] (not yet registered)."""
    wfinfo = ctx.wfs[wf]
    hours = _hours(wfinfo)
    data = ctx.ev.pickup_by_hour_code(wf, -400, -1, 0, 1e9)
    if not data:
        return []
    feats_of = {c: ctx.codes.feats(c) for c in {k[1] for k in data}}
    p_all = {}
    for h in hours:
        d = sum(v[0] for (hh, _), v in data.items() if hh == h)
        c = sum(v[1] for (hh, _), v in data.items() if hh == h)
        p_all[h] = c / d if d else 0.0
    scores = {}
    for f in FEATS:
        cells = defaultdict(lambda: defaultdict(lambda: [0.0, 0.0]))
        for (h, code), (d, c) in data.items():
            if h in p_all:
                x = cells[feats_of[code][f]][h]
                x[0] += d
                x[1] += c
        chi, df = 0.0, 0
        for v, by_h in cells.items():
            exp_tot = sum(d * p_all[h] for h, (d, _) in by_h.items())
            obs_tot = sum(c for _, c in by_h.values())
            if exp_tot <= 0:
                continue
            L = obs_tot / exp_tot
            for h, (d, c) in by_h.items():
                e = d * p_all[h] * L
                if e > 5:
                    chi += (c - e) ** 2 / (e * max(1 - p_all[h] * L, 0.05))
                    df += 1
            df -= 1
        df = max(df - (len(hours) - 1), 1)
        scores[f] = (chi - df) / math.sqrt(2 * df)
    strong = sorted([f for f, z in scores.items() if z > 3], key=lambda f: -scores[f])
    ctx.store.decide(ctx.now, wf, "schedule.partition_scores",
                     f"hour-profile difference by feature (z, >3 = real): "
                     + ", ".join(f"{f}={scores[f]:.1f}" for f in FEATS), {"scores": scores, "chosen": strong[:2]})
    if not strong:
        return []

    def cells_for(fs):
        agg = defaultdict(float)
        for (h, code), (d, _) in data.items():
            agg[tuple(feats_of[code][f] for f in fs)] += d
        return agg

    if len(strong) >= 2:
        fs = strong[:2]
        agg = cells_for(fs)
        good = {k: d for k, d in agg.items() if d >= S.SCHED_MIN_CELL_DIALS}
        if 2 <= len(good) <= S.SCHED_MAX_CELLS:
            return [{"where": {f: [v] for f, v in zip(fs, k)}, "dials": d} for k, d in sorted(good.items())]
    fs = strong[:1]
    agg = cells_for(fs)
    good = {k: d for k, d in agg.items() if d >= S.SCHED_MIN_CELL_DIALS}
    return [{"where": {fs[0]: [k[0]]}, "dials": d} for k, d in sorted(good.items())][: S.SCHED_MAX_CELLS]


def gamma(ctx, wf: str) -> float:
    return float(ctx.store.get_meta(f"sched_gamma:{wf}", S.SCHED_GAMMA))


def hour_tables(ctx, wf: str, cohorts: list[dict]) -> tuple[dict, dict]:
    """Hour weights for every cohort in `cohorts` (first-match membership). Returns (tables, dry_run)."""
    wfinfo = ctx.wfs[wf]
    g = gamma(ctx, wf)
    hours = _hours(wfinfo)
    today = ctx.now // 1440
    data = ctx.ev.pickup_by_hour_code(wf, today - 21, today, today, S.SCHED_HALF_LIFE_DAYS)
    if not data or not cohorts:
        return {}, {}
    member = {}
    for code in {k[1] for k in data}:
        member[code] = cohort_of(cohorts, ctx.codes.feats(code))
    p_all, tot = {}, defaultdict(lambda: [0.0, 0.0])
    by = defaultdict(lambda: defaultdict(lambda: [0.0, 0.0]))
    for (h, code), (d, c) in data.items():
        if h not in hours:
            continue
        tot[h][0] += d
        tot[h][1] += c
        x = by[member[code]][h]
        x[0] += d
        x[1] += c
    for h in hours:
        p_all[h] = tot[h][1] / tot[h][0] if tot[h][0] else 0.0
    tables, p_c, share = {}, {}, {}
    all_d = sum(v[0] for v in tot.values()) or 1.0
    for c in [x["id"] for x in cohorts] + ["default"]:
        bh = by.get(c)
        if not bh:
            continue
        exp_tot = sum(bh[h][0] * p_all[h] for h in hours)
        L = sum(bh[h][1] for h in hours) / exp_tot if exp_tot else 1.0
        share[c] = sum(bh[h][0] for h in hours) / all_d
        pc = {}
        for h in hours:
            d, y = bh[h]
            pc[h] = (y + S.SCHED_SHRINK_K * L * p_all[h]) / (d + S.SCHED_SHRINK_K)
        p_c[c] = pc
        if c == "default":
            continue
        tab = {}
        for h in hours:
            q = pc[h] / (L * p_all[h]) if p_all[h] > 0 and L > 0 else 1.0
            tab[str(h)] = round(min(max(q ** g, S.SCHED_W_MIN), S.SCHED_W_MAX), 2)
        tables[c] = tab
    # dry run: expected pickup per hour if hour-h capacity is drawn from cohorts in proportion share x weight
    # (ignores eligibility depletion => an upper bound; impact uses half of it)
    def expected(weights):
        vals = []
        for h in hours:
            num = den = 0.0
            for c, pc in p_c.items():
                w = weights.get(c, {}).get(str(h), 1.0)
                num += share[c] * w * pc[h]
                den += share[c] * w
            vals.append(num / den if den else 0.0)
        return sum(vals) / len(vals)
    before, after = expected({}), expected(tables)
    dry = {"method": "replay of last 21 days' pickup by hour x cohort (7-day half-life); hour-h capacity "
                     "drawn from cohorts in proportion to population share x weight; ignores eligibility depletion",
           "expected_pickup_flat": round(before, 4), "expected_pickup_new": round(after, 4),
           "relative_change": round(after / before - 1, 4) if before else 0.0, "gamma": g,
           "cohort_share": {k: round(v, 3) for k, v in share.items()}}
    return tables, dry


def table_distance(a: dict, b: dict) -> float:
    """Mean L1 distance between normalised hour tables over the union of cohorts."""
    keys = set(a) | set(b)
    if not keys:
        return 0.0
    tot = 0.0
    for k in keys:
        x, y = a.get(k) or {}, b.get(k) or {}
        hs = set(x) | set(y)
        sx = sum(x.values()) or 1.0
        sy = sum(y.values()) or 1.0
        tot += sum(abs(x.get(h, sx / max(len(hs), 1)) / sx - y.get(h, sy / max(len(hs), 1)) / sy) for h in hs)
    return tot / len(keys)


def guardrail_check(ctx, wf: str) -> dict | None:
    """Pickup since our last schedule change vs the 7 days before it. Returns a rollback reason or None.
    Used for every workflow: for engagement-primary flows pickup is the guardrail, for pickup-primary it is the
    KPI itself."""
    row = ctx.store.q("SELECT applied_minute FROM proposals WHERE workflow_id=? AND status='applied' AND "
                      "dims LIKE '%schedule%' ORDER BY applied_minute DESC LIMIT 1", (wf,))
    if not row or row[0][0] is None:
        return None
    t = row[0][0]
    today = ctx.now // 1440
    if today <= t // 1440 + 1:
        return None   # judge whole days only: the hour mix within a day is the thing we changed
    after_d, after_c = ctx.ev.pickup_total(wf, t // 1440 + 1, today - 1)
    before_d, before_c = ctx.ev.pickup_total(wf, t // 1440 - 7, t // 1440 - 1)
    if after_d < S.GUARDRAIL_CHECK_MIN_DIALS or before_d < S.GUARDRAIL_CHECK_MIN_DIALS:
        return None
    pa, pb = after_c / after_d, before_c / before_d
    from ..stats import z_two_prop
    z = z_two_prop(before_c, before_d, after_c, after_d)
    if pb - pa > 0.01 and z > 2.58:
        return {"pickup_before": round(pb, 4), "pickup_after": round(pa, 4), "z": round(z, 2)}
    return None


def engagement_guardrail(ctx, wf: str) -> dict | None:
    """For workflows whose guardrail is engagement: last 2 full days vs the pre-controller baseline (history).

    Better call timing reaches people sooner, so a larger share of connects comes from people who would only
    have been reached on a later attempt -- the engagement RATE can fall even though conclusions rise. The
    guardrail is on the rate, so we hold it: past 75% of the allowed drop we halve the sharpness of the hour
    weights (gamma); past 100% we halve it again."""
    g = ctx.wfs[wf]["objective"].get("guardrail") or {}
    limit = g.get("engagement_rate_max_drop")
    if limit is None:
        return None
    today = ctx.now // 1440
    if today < 2:
        return None
    base = ctx.store.get_meta(f"eng_baseline:{wf}")
    if base is None:
        c, _, e = ctx.ev.engagement(wf, -400 * 1440, 0)
        if c < 500:
            return None
        base = e / c
        ctx.store.set_meta(f"eng_baseline:{wf}", base)
    c, _, e = ctx.ev.engagement(wf, (today - 2) * 1440, today * 1440)
    if c < 500:
        return None
    rate = e / c
    drop = base - rate
    if drop > 0.75 * limit:
        return {"baseline": round(base, 4), "recent": round(rate, 4), "drop": round(drop, 4), "limit": limit,
                "connected": c}
    return None
