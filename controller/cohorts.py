"""The one shared cohort object (C2) and config helpers.

A cohort is (workflow_id, cohort_id, where). The same id is used in the live config, in detection queries,
in experiment state and in the supervisor view. Cohorts are never edited in place: a changed definition gets a
new id, so historical evidence always refers to exactly one population.

Config order is: variant segments first (more specific, evaluated first-match), then call-time cells.
"""
from __future__ import annotations

import copy
import json

from .ingest import FEATS
from .stats import tv

AGENT_DIMS = ("welcome_message", "voice", "caller_id")
CHANGE_DIMS = ("cohorts", "welcome_message", "voice", "caller_id", "prompt_version", "schedule")
SHORT = {"lang": "lang", "city_tier": "tier", "age_band": "age", "value_band": "value"}


def cohort_id(purpose: str, where: dict) -> str:
    parts = [f"{SHORT[f]}={'|'.join(where[f])}" for f in FEATS if f in where]
    return f"{'seg' if purpose == 'segment' else 'time'}.{'.'.join(parts)}"


def matches(where: dict, feats: dict) -> bool:
    return all(feats.get(f) in vals for f, vals in where.items())


def cohort_of(cohorts: list[dict], feats: dict) -> str:
    for c in cohorts:
        if matches(c["where"], feats):
            return c["id"]
    return "default"


def dist(cfg: dict, key: str, dim: str) -> dict:
    return (cfg["allocations"].get(key) or {}).get(dim) or cfg["allocations"]["default"][dim]


def changed_dims(old: dict, new: dict) -> list[str]:
    ch = set()
    if old.get("cohorts", []) != new.get("cohorts", []):
        ch.add("cohorts")
    keys = set(old["allocations"]) | set(new["allocations"]) | {c["id"] for c in old.get("cohorts", [])} \
        | {c["id"] for c in new.get("cohorts", [])}
    for d in AGENT_DIMS:
        if any(_norm(dist(old, k, d)) != _norm(dist(new, k, d)) for k in keys):
            ch.add(d)
    if old.get("prompt_version") != new.get("prompt_version"):
        ch.add("prompt_version")
    if _norm_sched(old.get("schedule")) != _norm_sched(new.get("schedule")):
        ch.add("schedule")
    return [d for d in CHANGE_DIMS if d in ch]


def max_shift(old: dict, new: dict) -> float:
    keys = {"default"} | {c["id"] for c in old.get("cohorts", [])} | {c["id"] for c in new.get("cohorts", [])}
    return max((tv(dist(old, k, d), dist(new, k, d)) for k in keys for d in AGENT_DIMS), default=0.0)


def _norm(d: dict) -> dict:
    s = sum(d.values()) or 1.0
    return {k: round(v / s, 6) for k, v in d.items() if v > 0}


def _norm_sched(s) -> str:
    s = s or {}
    hw = {k: {h: float(w) for h, w in v.items()} for k, v in (s.get("hour_weights") or {}).items()}
    return json.dumps({"hw": hw, "lph": s.get("lead_preferred_hour") or {}}, sort_keys=True)


class Registry:
    """Cohort definitions per workflow, persisted in the `cohorts` table."""

    def __init__(self, store):
        self.store = store

    def active(self, wf: str, purpose: str | None = None) -> list[dict]:
        sql = "SELECT cohort_id, where_json, purpose, created_minute, reason FROM cohorts " \
              "WHERE workflow_id=? AND status='active'"
        args = [wf]
        if purpose:
            sql += " AND purpose=?"
            args.append(purpose)
        rows = self.store.q(sql + " ORDER BY created_minute, cohort_id", args)
        return [{"id": r[0], "where": json.loads(r[1]), "purpose": r[2], "created_minute": r[3], "reason": r[4]}
                for r in rows]

    def add(self, wf: str, purpose: str, where: dict, minute: int, reason: str) -> str:
        cid = cohort_id(purpose, where)
        self.store.x("INSERT INTO cohorts VALUES (?,?,?,?, 'active', ?, ?) ON CONFLICT DO UPDATE SET "
                     "status='active'", (wf, cid, json.dumps(where), purpose, minute, reason))
        return cid

    def config_cohorts(self, wf: str) -> list[dict]:
        """Ordered list for the live config: segments first, then call-time cells."""
        segs = self.active(wf, "segment")
        cells = self.active(wf, "schedule")
        return [{"id": c["id"], "where": copy.deepcopy(c["where"])} for c in segs + cells]
