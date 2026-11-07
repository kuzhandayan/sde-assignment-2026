"""Planner: turns policy outputs into ONE batched proposal per workflow and picks the channel."""
from __future__ import annotations

import copy
import json

from . import settings as S
from .cohorts import AGENT_DIMS, changed_dims, cohort_of, dist, max_shift
from .policies import callerid, experiments, prompts, schedule
from .stats import normalise, tv

TERMINAL_BAD = ("rejected", "expired", "stale", "lapsed", "failed", "abandoned", "refused")


class Planner:
    def __init__(self, ctx, gov):
        self.ctx, self.gov = ctx, gov
        self.did_target: dict[str, dict] = {}

    # ------------------------------------------------------------------ helpers
    def frozen(self, wf):
        rows = self.ctx.store.q("SELECT dim, until_minute, sticky FROM frozen_dims WHERE workflow_id=?", (wf,))
        now = self.ctx.now
        return {d for d, u, s in rows if u > now}, {d for d, u, s in rows if s}

    def _info(self, wf):
        return self.ctx.wfs[wf]

    def _auto_policy(self, wf):
        return self._info(wf)["governance"]["auto_apply"]

    def _last(self, wf, purpose):
        r = self.ctx.store.q("SELECT status, submitted_minute FROM proposals WHERE workflow_id=? AND channel='approval'"
                             " AND purpose=? ORDER BY submitted_minute DESC LIMIT 1", (wf, purpose))
        return r[0] if r else (None, None)

    # ------------------------------------------------------------------ main entry
    def step(self, wf: str) -> None:
        ctx = self.ctx
        live = ctx.live(wf)
        self._incident(wf, live)
        if ctx.now % S.DID_REVIEW_EVERY_MIN == 0:
            self._caller_id(wf, ctx.live(wf))
        self._routine(wf, ctx.live(wf))

    # ------------------------------------------------------------------ A. prompt incidents
    def _incident(self, wf, live):
        ctx = self.ctx
        info = self._info(wf)
        fix = prompts.step(ctx, wf, live["config"], info["options"]["prompt_version"],
                           info["governance"]["min_validation_pass_rate"])
        if not fix:
            return
        if any(r["purpose"] == "incident" for r in self.gov.inflight(wf)):
            return
        st, at = self._last(wf, "incident")
        if st in TERMINAL_BAD and at is not None and ctx.now - at < 30:
            return
        ok, why = self.gov.can_submit(wf, ctx.now, urgent=True)
        if not ok:
            ctx.store.decide(ctx.now, wf, "incident.waiting", f"cannot submit fix yet: {why}", None)
            return
        cfg = copy.deepcopy(live["config"])
        cfg["prompt_version"] = fix["prompt"]
        reverting_supervisor = live["actor"] == "supervisor" or self._supervisor_set(wf, "prompt_version")
        body = self._body(wf, live, cfg, {
            "summary": [fix["summary"]],
            "why": [fix["rationale"]] + ([f"Note: this reverts a supervisor's prompt edit; it goes to your "
                                          f"approver, it is not applied behind anyone's back."]
                                         if reverting_supervisor else []),
            "impact": fix["impact"],
            "dry_run": {"prompt": {"method": "live flag rates per prompt on this workflow + validation run",
                                   "current": fix["detection"], "candidate": fix["candidate"],
                                   "validation": fix["validation"]}},
            "evidence": {"validation_run_id": fix["validation_run_id"], "incident_id": fix["incident_id"]},
        })
        row = self.gov.submit(wf, body, "incident", ["prompt_version"])
        if row["status"] in ("pending", "approved", "applied"):
            prompts.mark_proposed(ctx, wf, row["proposal_id"])

    def _supervisor_set(self, wf, dim):
        return bool(self.ctx.store.q1("SELECT 1 FROM frozen_dims WHERE workflow_id=? AND dim=?", (wf, dim)))

    # ------------------------------------------------------------------ B. caller ID
    def _caller_id(self, wf, live):
        ctx = self.ctx
        lo, hi = self._info(wf)["dialling_window"]
        if not (lo <= (ctx.now % 1440) // 60 < hi) and ctx.now != ctx.started_minute:
            return
        cur = dist(live["config"], "default", "caller_id")
        res = callerid.review(ctx, wf, cur)
        self.did_target[wf] = res
        if not res["urgent"]:
            return
        frozen, sticky = self.frozen(wf)
        target = normalise(res["target"])
        pol = self._auto_policy(wf)
        if pol.get("enabled") and "caller_id" in pol.get("allowed_dims", []) and "caller_id" not in sticky:
            self._auto_caller_id_step(wf, live, target, res["why"], urgent=True)
            return
        if any(r["purpose"] == "callerid" for r in self.gov.inflight(wf)):
            return
        ok, why = self.gov.can_submit(wf, ctx.now, urgent=True)
        if not ok:
            ctx.store.decide(ctx.now, wf, "callerid.waiting", f"bad caller ID but cannot submit: {why}", None)
            return
        cfg = copy.deepcopy(live["config"])
        cfg["allocations"]["default"]["caller_id"] = target
        body = self._body(wf, live, cfg, {"summary": [f"Stop dialling from a degraded number: caller ID -> "
                                                      f"{_fmt_dist(target)}"],
                                          "why": res["why"], "impact": None,
                                          "dry_run": {"caller_id": res["evidence"]}, "evidence": res["evidence"]})
        self.gov.submit(wf, body, "callerid", ["caller_id"])

    def _auto_caller_id_step(self, wf, live, target, why, urgent=False):
        pol = self._auto_policy(wf)
        cfg = copy.deepcopy(live["config"])
        cur = dist(cfg, "default", "caller_id")
        cfg["allocations"]["default"]["caller_id"] = _step_toward(cur, target, pol.get("max_shift", 0))
        if not changed_dims(live["config"], cfg):
            return
        body = self._body(wf, live, cfg, {
            "summary": [f"caller ID {_fmt_dist(cur)} -> {_fmt_dist(cfg['allocations']['default']['caller_id'])}"],
            "why": why or ["spread dialling across healthy caller IDs"], "impact": None,
            "dry_run": {"caller_id": (self.did_target.get(wf) or {}).get("evidence")},
            "evidence": {"caller_id": callerid.summary(self.ctx, wf)}})
        self.gov.auto(wf, body, "callerid" if urgent else "routine", ["caller_id"])

    # ------------------------------------------------------------------ C. routine
    def _routine(self, wf, live):
        ctx = self.ctx
        if ctx.now < 0:
            return
        auto_slot = self._auto_slot(wf)
        appr_ok, appr_why = self._approval_slot(wf)
        if not auto_slot and not appr_ok:
            return
        target, info = self.build_target(wf, live)
        dims = changed_dims(live["config"], target)
        if not dims:
            return
        # ---- auto part
        pol = self._auto_policy(wf)
        applied_now = ctx.store.q1("SELECT COUNT(*) FROM proposals WHERE workflow_id=? AND channel='auto' AND "
                                   "created_minute=?", (wf, ctx.now))
        if auto_slot and pol.get("enabled") and not self.gov.inflight(wf) and not applied_now:
            frozen, sticky = self.frozen(wf)
            allowed = [d for d in pol.get("allowed_dims", []) if d not in sticky and d not in frozen]
            auto_cfg = self._auto_part(wf, live, target, allowed, pol.get("max_shift", 0), info)
            adims = changed_dims(live["config"], auto_cfg)
            if adims:
                body = self._body(wf, live, auto_cfg, {**info, "summary": [info["summary_by_dim"].get(d, d)
                                                                           for d in adims],
                                                       "why": [info["why_by_dim"].get(d, d) for d in adims]})
                body["evidence"] = {d: info["evidence_by_dim"].get(d) for d in adims}
                self.gov.auto(wf, body, "routine", adims)
                ctx.store.set_meta(f"last_auto:{wf}", ctx.now)
                live = ctx.live(wf)
                target, info = self.build_target(wf, live)
                dims = changed_dims(live["config"], target)
        if not appr_ok or not dims:
            return
        # anything left that auto-apply can't do?
        need = [d for d in dims if not (pol.get("enabled") and d in pol.get("allowed_dims", []))]
        if not need:
            return
        st, at = self._last(wf, "routine")
        if (at is not None and st not in TERMINAL_BAD and ctx.now - at < 20 * 60 and not info.get("events")
                and "cohorts" not in need):
            return   # one routine request a day unless something happened (promotion, rollback, segment, stop)
        body = self._body(wf, live, target, info)
        self.gov.submit(wf, body, "routine", dims)
        ctx.store.set_meta(f"last_review:{wf}", ctx.now)

    def _auto_slot(self, wf) -> bool:
        ctx = self.ctx
        pol = self._auto_policy(wf)
        if not pol.get("enabled"):
            return False
        last = ctx.store.get_meta(f"last_auto:{wf}")
        lo, hi = self._info(wf)["dialling_window"]
        h = (ctx.now % 1440) // 60
        in_window = (lo - 1) <= h < hi
        return in_window and (last is None or ctx.now - last >= 180)

    def _approval_slot(self, wf):
        ctx = self.ctx
        if self.gov.inflight(wf):
            return False, "approval in flight"
        ok, why = self.gov.can_submit(wf, ctx.now, urgent=False)
        if not ok:
            return False, why
        st, at = self._last(wf, "routine")
        if at is not None:
            gap = S.REPROPOSE_AFTER_REJECT_MIN if st in TERMINAL_BAD else 360
            if ctx.now - at < gap:
                return False, "spacing"
        last = ctx.store.get_meta(f"last_review:{wf}")
        if last is not None and ctx.now - last < 120:
            return False, "reviewed recently"
        ctx.store.set_meta(f"last_review:{wf}", ctx.now)
        return True, "ok"

    # ------------------------------------------------------------------ desired config
    def build_target(self, wf: str, live: dict) -> tuple[dict, dict]:
        ctx = self.ctx
        info_wf = self._info(wf)
        cfg = copy.deepcopy(live["config"])
        frozen, sticky = self.frozen(wf)
        info = {"summary": [], "why": [], "summary_by_dim": {}, "why_by_dim": {}, "evidence_by_dim": {},
                "dry_run": {}, "evidence": {}, "impact_parts": {}}
        reg_ids = {r[0] for r in ctx.store.q("SELECT cohort_id FROM cohorts WHERE workflow_id=?", (wf,))}
        # experiments run on every workflow (engagement is the KPI or the guardrail)
        engagement_primary = True

        # ---- 1. cohorts (+ segment discovery)
        if "cohorts" not in frozen:
            if engagement_primary:
                self._maybe_new_segment(wf, cfg, info)
            reg = ctx.registry.config_cohorts(wf)
            foreign = [c for c in cfg.get("cohorts", []) if c["id"] not in reg_ids]
            segs = [c for c in reg if c["id"].startswith("seg.")]
            cells = [c for c in reg if not c["id"].startswith("seg.")]
            new = (segs + foreign + cells)[:20]
            if new != cfg.get("cohorts", []):
                old_ids = {c["id"] for c in cfg.get("cohorts", [])}
                added = [c["id"] for c in new if c["id"] not in old_ids]
                cfg["cohorts"] = new
                ids = {c["id"] for c in new}
                for k in list(cfg["allocations"]):
                    if k != "default" and k not in ids:
                        del cfg["allocations"][k]
                hw = cfg["schedule"].setdefault("hour_weights", {})
                for k in list(hw):
                    if k != "default" and k not in ids:
                        del hw[k]
                if added:
                    s = f"add cohorts {', '.join(added)}"
                    info["summary"].append(s)
                    info["summary_by_dim"]["cohorts"] = s
                    info["why_by_dim"]["cohorts"] = "shared cohort definitions (see registry reasons)"
                    for c in added:
                        r = ctx.store.q1("SELECT reason FROM cohorts WHERE workflow_id=? AND cohort_id=?", (wf, c))
                        if r:
                            info["why"].append(f"{c}: {r}")

        # ---- 2. welcome/voice experiments
        if engagement_primary:
            self._experiments(wf, cfg, frozen, info)

        # ---- 3. caller ID
        if "caller_id" not in frozen:
            res = self.did_target.get(wf)
            if res is None and ctx.now % S.DID_REVIEW_EVERY_MIN != 0:
                res = callerid.review(ctx, wf, dist(cfg, "default", "caller_id"))
                self.did_target[wf] = res
            if res:
                cur = dist(cfg, "default", "caller_id")
                tgt = normalise(res["target"])
                if tv(cur, tgt) >= 0.02:
                    cfg["allocations"]["default"]["caller_id"] = tgt
                    s = f"caller ID {_fmt_dist(cur)} -> {_fmt_dist(tgt)}"
                    info["summary"].append(s)
                    info["summary_by_dim"]["caller_id"] = s
                    w = "; ".join(res["why"]) or "spread load equally across healthy numbers; probe unknown ones"
                    info["why"].append(w)
                    info["why_by_dim"]["caller_id"] = w
                    info["evidence_by_dim"]["caller_id"] = callerid.summary(ctx, wf)
                    info["dry_run"]["caller_id"] = {"status": callerid.summary(ctx, wf),
                                                    "windows": res.get("evidence")}

        # ---- 4. call-time schedule
        if "schedule" not in frozen:
            self._schedule(wf, live, cfg, info)
        return cfg, info

    def _maybe_new_segment(self, wf, cfg, info):
        ctx = self.ctx
        segs = ctx.registry.active(wf, "segment")
        rows = ctx.ev.load_eng(wf, ctx.now // 1440 - 6, ctx.now // 1440)
        t = experiments.discover_segment(ctx, wf, rows, segs, {d: dist(cfg, "default", d) for d in experiments.DIMS})
        if not t:
            return
        cid = ctx.registry.add(wf, "segment", t["where"], ctx.now, t["why"])
        base = ctx.store.get_meta(f"default_cfg:{wf}") or cfg
        ctl = dist(base, "default", t["dim"])
        experiments._save(ctx, wf, cid, t["dim"], {
            "status": "exploring", "control": max(ctl, key=ctl.get), "suspended": {}, "started_minute": ctx.now,
            "log": [[ctx.now, "start", t["why"]]]})
        ctx.store.decide(ctx.now, wf, "cohort.segment_added", t["why"], t)
        info.setdefault("events", []).append(f"segment:{cid}")

    def _experiments(self, wf, cfg, frozen, info):
        ctx = self.ctx
        rows = ctx.ev.load_eng(wf, ctx.now // 1440 - 10, ctx.now // 1440)
        segs = [c for c in ctx.registry.active(wf, "segment") if any(x["id"] == c["id"] for x in cfg["cohorts"])]
        base = ctx.store.get_meta(f"default_cfg:{wf}") or cfg
        stats_by_key = {}
        for dim in experiments.DIMS:
            if dim in frozen:
                continue
            ctl_dist = dist(base, "default", dim)
            control = max(ctl_dist, key=ctl_dist.get)
            keys = ["default"] + [s["id"] for s in segs]
            for key in keys:
                if key != "default" and experiments._state(ctx, wf, key, dim)["status"] == "idle":
                    continue   # a segment only owns the dim it was created for
                codes = experiments.population(ctx, wf, key, dim, segs)
                res = experiments.review_key(ctx, wf, key, dim, rows, codes, control, cfg)
                stats_by_key.setdefault(key, {})[dim] = res["stats"]
                if res.get("event") or any("suspend" in w for w in res.get("why", [])):
                    info.setdefault("events", []).append(f"{key}/{dim}:{res.get('event') or 'suspend'}")
                tgt = res.get("target")
                if not tgt:
                    continue
                cur = dist(cfg, key, dim)
                if tv(cur, tgt) < S.EXP_MIN_CHANGE_TV and not res.get("event") and \
                        not (res.get("why") and any("suspend" in w for w in res["why"])):
                    continue
                if tv(cur, tgt) < 1e-6:
                    continue
                cfg["allocations"].setdefault(key, {})[dim] = tgt
                s = f"{key}/{dim}: {_fmt_dist(cur)} -> {_fmt_dist(tgt)}"
                info["summary"].append(s)
                info["summary_by_dim"][dim] = "; ".join(filter(None, [info["summary_by_dim"].get(dim), s]))
                w = "; ".join(res["why"]) or (f"{key}/{dim}: allocation follows P(best) "
                                              f"{res.get('p_best')} with a 10% floor per live arm")
                info["why"].append(w)
                info["why_by_dim"][dim] = "; ".join(filter(None, [info["why_by_dim"].get(dim), w]))
                info["evidence_by_dim"].setdefault(dim, {})[key] = {"stats": res["stats"], "p_best": res.get("p_best")}
                # dry run: expected engagement under new vs current allocation, from measured arm rates
                e_old = experiments.expected_engagement({dim: res["stats"]}, {dim: cur})
                e_new = experiments.expected_engagement({dim: res["stats"]}, {dim: tgt})
                codes_n, tot = ctx.ev.connected_share(wf, ctx.now // 1440, codes)
                share = codes_n / tot if tot else 0.0
                rel = (e_new / e_old - 1) if e_old else 0.0
                info["dry_run"][f"{key}/{dim}"] = {
                    "method": "post-stratified engagement per arm over the last 10 days (1.5-day half-life), "
                              "applied to the cohort's share of connected calls",
                    "arm_engagement": {a: s.get("rate") for a, s in res["stats"].items()},
                    "arm_connected": {a: s.get("raw_n") for a, s in res["stats"].items()},
                    "expected_relative_engagement_change_in_cohort": round(rel, 4),
                    "cohort_share_of_connected": round(share, 3)}
                info["impact_parts"][f"{key}/{dim}"] = rel * share
        info["evidence"]["experiments"] = stats_by_key

    def _schedule(self, wf, live, cfg, info):
        ctx = self.ctx
        cells = [c for c in cfg.get("cohorts", [])]
        if not cells:
            return
        disabled_until = ctx.store.get_meta(f"schedule_disabled:{wf}")
        if disabled_until and ctx.now < disabled_until:
            return
        g = schedule.guardrail_check(ctx, wf)
        if g:
            cfg["schedule"]["hour_weights"] = {}
            ctx.store.set_meta(f"schedule_disabled:{wf}", ctx.now + 3 * 1440)
            s = "remove call-time weights (pickup fell after the last schedule change)"
            msg = (f"pickup {g['pickup_before']:.1%} -> {g['pickup_after']:.1%} after call-time weights "
                   f"(z={g['z']}); rolling back to flat")
            ctx.store.decide(ctx.now, wf, "schedule.rollback", msg, g)
            info["summary"].append(s)
            info["why"].append(msg)
            info["summary_by_dim"]["schedule"] = s
            info["why_by_dim"]["schedule"] = msg
            return
        eg = schedule.engagement_guardrail(ctx, wf)
        last_g = ctx.store.get_meta(f"sched_gamma_changed:{wf}")
        if eg and (last_g is None or ctx.now - last_g >= 1440):
            g_old = schedule.gamma(ctx, wf)
            g_new = max(round(g_old / 2, 2), 0.5)
            if g_new < g_old:
                ctx.store.set_meta(f"sched_gamma:{wf}", g_new)
                ctx.store.set_meta(f"sched_gamma_changed:{wf}", ctx.now)
                msg = (f"engagement {eg['recent']:.1%} vs {eg['baseline']:.1%} before the controller "
                       f"(drop {eg['drop']:.3f}, guardrail {eg['limit']}): softening call-time weights, "
                       f"gamma {g_old} -> {g_new}")
                ctx.store.decide(ctx.now, wf, "guardrail.engagement", msg, eg)
                info["why"].append(msg)
        tables, dry = schedule.hour_tables(ctx, wf, cfg["cohorts"])
        if not tables:
            return
        cur = (live["config"].get("schedule") or {}).get("hour_weights") or {}
        ids = {c["id"] for c in cfg["cohorts"]}
        keep = {k: v for k, v in cur.items() if k not in tables and (k in ids or k == "default")}
        new = {**keep, **tables}
        cohorts_changed = cfg["cohorts"] != live["config"].get("cohorts", [])
        if not cohorts_changed and schedule.table_distance(new, cur) < S.SCHED_MIN_CHANGE_L1:
            return
        cfg["schedule"]["hour_weights"] = new
        s = f"call-time weights for {len(tables)} cohorts (expected pickup {dry['expected_pickup_flat']:.1%} -> " \
            f"{dry['expected_pickup_new']:.1%})"
        w = ("call each cohort more in the hours where it picks up relatively better, measured on "
             "history; the dialler's capacity per hour is unchanged and no cohort is called more overall")
        info["summary"].append(s)
        info["why"].append(w)
        info["summary_by_dim"]["schedule"] = s
        info["why_by_dim"]["schedule"] = w
        info["evidence_by_dim"]["schedule"] = dry
        info["dry_run"]["schedule"] = dry
        info["impact_parts"]["schedule_pickup"] = 0.5 * dry["relative_change"]

    def _auto_part(self, wf, live, target, allowed, max_sh, info) -> dict:
        """Live config + only the auto-permitted dims of `target`, each agent dim stepped by <= max_shift."""
        cfg = copy.deepcopy(live["config"])
        live_ids = {c["id"] for c in cfg.get("cohorts", [])}
        for dim in ("welcome_message", "voice", "caller_id"):
            if dim not in allowed:
                continue
            for key in ["default"] + sorted(live_ids):
                if key != "default" and key not in target["allocations"]:
                    continue
                if key != "default" and dim not in (target["allocations"].get(key) or {}):
                    continue
                cur, tgt = dist(cfg, key, dim), dist(target, key, dim)
                if tv(cur, tgt) < 1e-6:
                    continue
                cfg["allocations"].setdefault(key, {})[dim] = _step_toward(cur, tgt, max_sh)
        if "schedule" in allowed:
            if target.get("cohorts", []) == cfg.get("cohorts", []):
                cfg["schedule"] = copy.deepcopy(target["schedule"])
            elif cfg.get("cohorts"):
                tables, _ = schedule.hour_tables(self.ctx, wf, cfg["cohorts"])
                cur = (cfg.get("schedule") or {}).get("hour_weights") or {}
                if tables and schedule.table_distance({**cur, **tables}, cur) >= S.SCHED_MIN_CHANGE_L1:
                    cfg["schedule"]["hour_weights"] = {**cur, **tables}
        if "prompt_version" in allowed:
            cfg["prompt_version"] = target["prompt_version"]
        if "cohorts" in allowed and target.get("cohorts") != cfg.get("cohorts"):
            return copy.deepcopy(target) if max_shift(live["config"], target) <= max_sh + 1e-9 else cfg
        # final guard: never exceed the policy's max_shift
        if max_shift(live["config"], cfg) > max_sh + 1e-9:
            for dim in AGENT_DIMS:
                for key in list(cfg["allocations"]):
                    if dim in cfg["allocations"][key]:
                        cfg["allocations"][key][dim] = _step_toward(dist(live["config"], key, dim),
                                                                    cfg["allocations"][key][dim], max_sh * 0.99)
        return cfg

    # ------------------------------------------------------------------ the request a supervisor reads
    def _body(self, wf, live, cfg, info) -> dict:
        ctx = self.ctx
        old = live["config"]
        dims = changed_dims(old, cfg)
        diff = _diff(old, cfg, dims)
        affected = self._affected(wf, old, cfg, dims)
        if info.get("impact") is not None:
            impact = info["impact"]
        else:
            primary = sum(info.get("impact_parts", {}).values())
            impact = min(max(primary / S.IMPACT_FULL_SCALE, 0.0), 1.0)
        impact = round(max(impact, 0.01), 3)
        summary = "; ".join(info["summary"]) or "configuration update"
        frozen, sticky = self.frozen(wf)
        touched = [d for d in dims if d in sticky]
        if touched:
            note = f"CHANGES A SUPERVISOR EDIT ({', '.join(touched)}) -- "
            summary = note + summary
            info["why"].insert(0, f"This request changes {', '.join(touched)}, which a supervisor edited; we left "
                                  f"it untouched for 24h and are asking rather than changing it ourselves.")
        if len(summary) > 280:
            summary = summary[:277] + "..."
        dry = info.get("dry_run") or {"note": "no measurable effect expected"}
        dry["affected_leads_method"] = "active leads (running campaigns, not concluded) whose served variant " \
                                       "distribution, hour weight or prompt changes"
        return {"base_version": live["version"], "proposed_config": cfg, "change_summary": summary, "diff": diff,
                "affected_leads": int(affected), "dry_run": dry, "impact_score": impact,
                "rationale": " | ".join(info["why"]) or summary,
                "evidence": info.get("evidence") or {"note": "see dry_run"},
                "expires_in_hours": self._info(wf)["governance"]["proposal_ttl_hours"]}

    def _affected(self, wf, old, new, dims) -> int:
        ctx = self.ctx
        cad = len(self._info(wf)["cadence"])
        by_code = ctx.ev.active_leads_by_code(wf, ctx.now // 1440, cad)
        if "prompt_version" in dims:
            return sum(by_code.values())
        n = 0
        ho = (old.get("schedule") or {}).get("hour_weights") or {}
        hn = (new.get("schedule") or {}).get("hour_weights") or {}
        for code, k in by_code.items():
            f = ctx.codes.feats(code)
            co, cn = cohort_of(old.get("cohorts", []), f), cohort_of(new.get("cohorts", []), f)
            changed = any(dist(old, co, d) != dist(new, cn, d) for d in AGENT_DIMS)
            to = ho.get(co) if co in ho else ho.get("default")
            tn = hn.get(cn) if cn in hn else hn.get("default")
            if changed or to != tn:
                n += k
        return n


# ------------------------------------------------------------------------------------------ utilities
def _step_toward(cur: dict, tgt: dict, max_tv: float) -> dict:
    d = tv(cur, tgt)
    if d <= max_tv + 1e-9:
        return normalise(tgt)
    lam = max_tv / d
    keys = set(cur) | set(tgt)
    sc, st = sum(cur.values()) or 1, sum(tgt.values()) or 1
    out = {k: (1 - lam) * cur.get(k, 0) / sc + lam * tgt.get(k, 0) / st for k in keys}
    res = normalise(out)
    # rounding can push TV a hair over the limit
    while tv(cur, res) > max_tv + 1e-9 and lam > 0:
        lam *= 0.98
        res = normalise({k: (1 - lam) * cur.get(k, 0) / sc + lam * tgt.get(k, 0) / st for k in keys})
    return res


def _fmt_dist(d: dict) -> str:
    return "{" + ", ".join(f"{k} {v:.0%}" for k, v in sorted(d.items())) + "}"


def _diff(old, new, dims) -> dict:
    out = {}
    if "cohorts" in dims:
        oi = {c["id"]: c for c in old.get("cohorts", [])}
        ni = {c["id"]: c for c in new.get("cohorts", [])}
        out["cohorts"] = {"added": [ni[k] for k in ni if k not in oi], "removed": [k for k in oi if k not in ni],
                          "order": list(ni)}
    for d in ("welcome_message", "voice", "caller_id"):
        if d in dims:
            # only keys that carry their own distribution (cohorts without one inherit `default`)
            keys = ["default"] + [c["id"] for c in new.get("cohorts", [])
                                  if d in (new["allocations"].get(c["id"]) or {}) or d in (old["allocations"].get(c["id"]) or {})]
            out[d] = {k: {"from": dist(old, k, d), "to": dist(new, k, d)} for k in keys
                      if dist(old, k, d) != dist(new, k, d)}
    if "prompt_version" in dims:
        out["prompt_version"] = {"from": old["prompt_version"], "to": new["prompt_version"]}
    if "schedule" in dims:
        ho = (old.get("schedule") or {}).get("hour_weights") or {}
        hn = (new.get("schedule") or {}).get("hour_weights") or {}
        out["schedule.hour_weights"] = {k: {"from": ho.get(k), "to": hn.get(k)}
                                        for k in set(ho) | set(hn) if ho.get(k) != hn.get(k)}
    return out or {"note": "no-op"}
