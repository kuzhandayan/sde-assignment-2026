"""Read models over the aggregates. Every policy reads evidence through here, so 'what counts as evidence' is
defined once: only calls that actually happened, with the variant they actually got (stakeholders/05)."""
from __future__ import annotations

from collections import defaultdict

from .cohorts import matches
from .ingest import Codes


class Evidence:
    def __init__(self, store, codes: Codes):
        self.store, self.codes = store, codes

    # ------------------------------------------------------------------ helpers
    def code_filter(self, where: dict | None, exclude: list[dict] | None = None):
        """Set of code ids matching `where` and none of `exclude` (None = all codes)."""
        out = set()
        for cid, t in self.codes.by_id.items():
            f = self.codes.feats(cid)
            if where is not None and not matches(where, f):
                continue
            if exclude and any(matches(w, f) for w in exclude):
                continue
            out.add(cid)
        return out

    # ------------------------------------------------------------------ engagement by arm
    def arm_stats(self, wf: str, dim: str, today: int, half_life: float, codes: set | None = None,
                  since_day: int | None = None, until_day: int | None = None, contrast_only: bool = True) -> dict:
        """Post-stratified engagement per arm of `dim`.

        Strata = (day, config version, config cohort). Within a stratum every arm was assigned at random to the
        same population, so per-stratum arm rates are unbiased; combining strata with weights N_s x decay keeps
        populations aligned across arms even when allocations changed over time (no Simpson's paradox).
        Returns {arm: {"n": discounted connected, "raw_n", "raw_y", "rate"}}.
        """
        rows = self.load_eng(wf, since_day if since_day is not None else today - 10,
                             until_day if until_day is not None else 10 ** 6)
        return arm_stats_from(rows, dim, today, half_life, codes, contrast_only)

    def load_eng(self, wf: str, lo_day: int, hi_day: int) -> list[tuple]:
        """(day, version, cohort, code, wm, vo, conn, eng) rows -- load once, slice many times."""
        return self.store.q("SELECT day, version, cohort, code_id, wm, vo, conn, eng FROM agg_eng "
                            "WHERE workflow_id=? AND day>=? AND day<=?", (wf, lo_day, hi_day))


    def connected_share(self, wf: str, today: int, codes: set) -> tuple[float, float]:
        """(connected calls in `codes`, total connected) over the last 3 days."""
        rows = self.store.q("SELECT code_id, SUM(conn) FROM agg_eng WHERE workflow_id=? AND day>=? GROUP BY code_id",
                            (wf, today - 3))
        tot = sum(r[1] for r in rows)
        sub = sum(r[1] for r in rows if r[0] in codes)
        return sub, tot

    def engagement(self, wf: str, lo_min: int, hi_min: int, prompt: str | None = None) -> tuple[int, int, int]:
        """(connected, flags, engaged) between two sim minutes (30-min resolution)."""
        sql = "SELECT COALESCE(SUM(conn),0), COALESCE(SUM(flags),0), COALESCE(SUM(eng),0) FROM agg_qa " \
              "WHERE workflow_id=? AND slot>=? AND slot<?"
        args = [wf, lo_min // 30, hi_min // 30]
        if prompt:
            sql += " AND prompt=?"
            args.append(prompt)
        r = self.store.q(sql, args)[0]
        return int(r[0]), int(r[1]), int(r[2])

    def qa_by_prompt(self, wf: str, lo_min: int, hi_min: int) -> dict:
        rows = self.store.q("SELECT prompt, SUM(conn), SUM(flags), SUM(eng) FROM agg_qa WHERE workflow_id=? "
                            "AND slot>=? AND slot<? GROUP BY prompt", (wf, lo_min // 30, hi_min // 30))
        return {p: (int(c), int(f), int(e)) for p, c, f, e in rows}

    # ------------------------------------------------------------------ pickup
    def pickup_by_hour_code(self, wf: str, lo_day: int, hi_day: int, today: int, half_life: float) -> dict:
        """{(hour, code): [discounted dials, discounted connected]}"""
        rows = self.store.q("SELECT day, hour, code_id, SUM(dials), SUM(conn) FROM agg_pick WHERE workflow_id=? "
                            "AND day>=? AND day<=? GROUP BY day, hour, code_id", (wf, lo_day, hi_day))
        out: dict[tuple, list] = defaultdict(lambda: [0.0, 0.0])
        for day, h, code, d, c in rows:
            w = 0.5 ** (max(today - day, 0) / half_life)
            o = out[(h, code)]
            o[0] += w * d
            o[1] += w * c
        return out

    def pickup_by_did(self, wf: str, lo_min: int, hi_min: int) -> dict:
        """{did: (dials, connected)} between two sim minutes (hour resolution)."""
        rows = self.store.q("SELECT did, SUM(dials), SUM(conn) FROM agg_pick WHERE workflow_id=? AND "
                            "day>=? AND day<=? AND (day*24+hour) >= ? AND (day*24+hour) < ? GROUP BY did",
                            (wf, lo_min // 1440, hi_min // 1440, lo_min // 60, -(-hi_min // 60)))
        return {d: (int(n), int(c)) for d, n, c in rows}

    def pickup_total(self, wf: str, lo_day: int, hi_day: int) -> tuple[int, int]:
        r = self.store.q("SELECT COALESCE(SUM(dials),0), COALESCE(SUM(conn),0) FROM agg_pick WHERE workflow_id=? "
                         "AND day>=? AND day<=?", (wf, lo_day, hi_day))[0]
        return int(r[0]), int(r[1])

    # ------------------------------------------------------------------ leads
    def active_leads_by_code(self, wf: str, today: int, cadence_days: int) -> dict:
        """Leads still in a running campaign and not concluded, by feature code (an upper bound: leads whose
        attempts are exhausted for the day are still counted)."""
        rows = self.store.q("SELECT code_id, SUM(uploaded - concluded) FROM campaign_leads WHERE workflow_id=? "
                            "AND cday > ? GROUP BY code_id", (wf, today - cadence_days))
        return {c: max(int(n), 0) for c, n in rows}


def arm_stats_from(rows, dim: str, today: int, half_life: float, codes: set | None = None,
                   contrast_only: bool = True) -> dict:
    """See Evidence.arm_stats. Pure function over load_eng() rows."""
    ai = 4 if dim == "welcome_message" else 5
    strata: dict[tuple, dict] = defaultdict(lambda: defaultdict(lambda: [0, 0]))
    for r in rows:
        if codes is not None and r[3] not in codes:
            continue
        c = strata[(r[0], r[1], r[2])][r[ai]]
        c[0] += r[6]
        c[1] += r[7]
    num, den, neff, rn, ry = (defaultdict(float) for _ in range(5))
    for (day, _, _), arms in strata.items():
        live = [a for a, c in arms.items() if c[0] > 0]
        if contrast_only and len(live) < 2:
            continue
        w = 0.5 ** (max(today - day, 0) / half_life)
        N = sum(c[0] for c in arms.values())
        for a, (n, y) in arms.items():
            if n < 3:
                continue
            num[a] += w * N * (y / n)
            den[a] += w * N
            neff[a] += w * n
            rn[a] += n
            ry[a] += y
    return {a: {"n": neff[a], "raw_n": rn[a], "raw_y": ry[a], "rate": num[a] / den[a] if den[a] else None}
            for a in den}
