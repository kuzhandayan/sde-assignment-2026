"""Unit tests for the controller's load-bearing pieces."""
import json

import pytest

from controller import stats
from controller.api import ApiResult
from controller.cohorts import changed_dims, cohort_of, max_shift
from controller.data import arm_stats_from
from controller.governance import Governance
from controller.ingest import Ingestor
from controller.planner import _step_toward
from controller.store import Store


# ------------------------------------------------------------------------------------------------ stats
def test_prob_best_is_deterministic_and_sensible():
    a = stats.prob_best([60, 40], [40, 60], seed=1)
    assert a == stats.prob_best([60, 40], [40, 60], seed=1)
    assert a[0] > 0.99


def test_holm_and_binomial():
    assert stats.holm([0.01, 0.04], 0.05) == [True, True]
    assert stats.holm([0.03, 0.04], 0.05) == [False, False]
    assert stats.binom_upper_p(30, 1000, 0.015) < 1e-3
    assert stats.binom_upper_p(15, 1000, 0.015) > 0.3
    lo, hi = stats.wilson(99, 100)
    assert lo < 0.99 < hi


def test_step_toward_respects_max_shift():
    cur, tgt = {"W1": 1.0}, {"W1": 0.2, "W2": 0.4, "W3": 0.4}
    out = _step_toward(cur, tgt, 0.2)
    assert stats.tv(cur, out) <= 0.2 + 1e-9
    assert out["W1"] < 1.0


# ------------------------------------------------------------------------------------------------ cohorts
def _cfg(**kw):
    c = {"cohorts": [], "allocations": {"default": {"welcome_message": {"W1": 1}, "voice": {"V1": 1},
                                                    "caller_id": {"D1": 1}}},
         "prompt_version": "P1", "schedule": {"hour_weights": {}, "lead_preferred_hour": {}}}
    c.update(kw)
    return c


def test_changed_dims_and_shift():
    a = _cfg()
    b = _cfg()
    b["allocations"]["default"]["voice"] = {"V1": 0.5, "V2": 0.5}
    b["prompt_version"] = "P3"
    assert changed_dims(a, b) == ["voice", "prompt_version"]
    assert max_shift(a, b) == pytest.approx(0.5)


def test_first_match_cohorts():
    cs = [{"id": "seg", "where": {"lang": ["ta"], "age_band": ["60+"]}}, {"id": "old", "where": {"age_band": ["60+"]}}]
    assert cohort_of(cs, {"lang": "ta", "age_band": "60+"}) == "seg"
    assert cohort_of(cs, {"lang": "hi", "age_band": "60+"}) == "old"
    assert cohort_of(cs, {"lang": "hi", "age_band": "18-30"}) == "default"


# ------------------------------------------------------------------------------------------------ evidence
def test_post_stratification_avoids_simpsons_paradox():
    # stratum 1: high-engagement population, mostly arm B; stratum 2: low-engagement, mostly arm A.
    # A is better within BOTH strata; pooled counts would say B is better.
    rows = [
        # day, version, cohort, code, wm, vo, conn, eng
        (0, 1, "c1", 1, "A", "V1", 100, 90), (0, 1, "c1", 1, "B", "V1", 900, 720),
        (0, 1, "c2", 2, "A", "V1", 900, 360), (0, 1, "c2", 2, "B", "V1", 100, 30),
    ]
    pooled_a, pooled_b = (90 + 360) / 1000, (720 + 30) / 1000
    assert pooled_b > pooled_a
    s = arm_stats_from(rows, "welcome_message", today=0, half_life=1e9)
    assert s["A"]["rate"] > s["B"]["rate"]


# ------------------------------------------------------------------------------------------------ ingestion
class FakeChunks:
    def __init__(self, chunks):
        self.chunks = chunks

    def list_chunks(self, kind, after):
        return [m for m, _ in self.chunks if m["kind"] == kind and m["chunk"] > after]

    def chunk_text(self, n):
        return next(t for m, t in self.chunks if m["chunk"] == n)


def _lead(pid, lang="hi"):
    return json.dumps({"type": "lead", "ts": "2027-01-04T08:00:00+05:30", "workflow_id": "wf", "campaign_id": "wf:c1",
                       "lead_id": f"wf:l{pid}", "person_id": f"wf:p{pid:07d}",
                       "features": {"lang": lang, "city_tier": "1", "age_band": "60+", "value_band": "mid"}})


def _call(pid, eid, conn=True, eng=True):
    return json.dumps({"type": "call", "ts": "2027-01-04T10:07:00+05:30", "workflow_id": "wf", "campaign_id": "wf:c1",
                       "lead_id": f"wf:l{pid}", "person_id": f"wf:p{pid:07d}", "attempt_no": 1,
                       "campaign_day_index": 0, "config_version": 1, "cohort_id": "default",
                       "variant": {"welcome_message": "W1", "voice": "V1", "caller_id": "D1", "prompt_version": "P1"},
                       "connected": conn, "engaged": eng and conn, "event_id": eid,
                       "qa": {"hallucination_flag": False, "flow_adherence": 0.9} if conn else None})


def test_ingestion_is_exactly_once_across_restarts(tmp_path):
    text = "\n".join([_lead(1), _lead(2, "ta"), _call(1, 3), _call(2, 4, conn=False)])
    api = FakeChunks([({"chunk": 0, "kind": "events", "first_event_id": 1, "last_event_id": 4}, text)])
    db = tmp_path / "c.db"
    Ingestor(api, Store(db)).run()
    Ingestor(api, Store(db)).run()      # restart: chunk already committed -> skipped
    s = Store(db)
    assert s.q1("SELECT SUM(dials) FROM agg_pick") == 2
    assert s.q1("SELECT SUM(conn) FROM agg_eng") == 1
    assert s.q1("SELECT COUNT(*) FROM chunks_done") == 1


def test_crash_mid_chunk_leaves_nothing(tmp_path, monkeypatch):
    text = "\n".join([_lead(1), _call(1, 2)])
    api = FakeChunks([({"chunk": 0, "kind": "events"}, text)])
    db = tmp_path / "c.db"
    ing = Ingestor(api, Store(db))
    import controller.ingest as mod

    def boom(name):
        raise KeyboardInterrupt
    monkeypatch.setattr(mod, "crashpoint", boom)
    with pytest.raises(KeyboardInterrupt):
        ing.run()
    s = Store(db)
    assert s.q1("SELECT COUNT(*) FROM chunks_done") == 0
    assert s.q1("SELECT COUNT(*) FROM agg_pick") == 0
    monkeypatch.setattr(mod, "crashpoint", lambda n: None)
    Ingestor(api, Store(db)).run()
    assert Store(db).q1("SELECT SUM(dials) FROM agg_pick") == 1


# ------------------------------------------------------------------------------------------------ governance
class FakeGovAPI:
    def __init__(self):
        self.approvals = {}
        self.version = 1
        self.apply_calls = 0
        self.history = [{"version": 1, "proposal_id": None, "approval_id": None, "actor": "business_default"}]

    def request_approval(self, body):
        if any(a["proposal_id"] == body["proposal_id"] for a in self.approvals.values()):
            return ApiResult(409, {"error": "duplicate_proposal_id"})
        aid = f"apr_{len(self.approvals) + 1:05d}"
        self.approvals[aid] = {"approval_id": aid, "proposal_id": body["proposal_id"], "status": "pending",
                               "workflow_id": body["workflow_id"]}
        return ApiResult(200, dict(self.approvals[aid]))

    def list_approvals(self, wid=None, status=None):
        return [dict(a) for a in self.approvals.values()]

    def apply(self, wid, aid):
        self.apply_calls += 1
        self.version += 1
        self.approvals[aid]["status"] = "applied"
        self.history.append({"version": self.version, "proposal_id": self.approvals[aid]["proposal_id"],
                             "approval_id": aid, "actor": "controller_approved"})
        return ApiResult(200, {"version": self.version})

    def config_history(self, wid):
        return self.history

    def config(self, wid):
        return {"version": self.version, "actor": "x", "applied_at": None, "config": _cfg()}


class FakeCtx:
    def __init__(self, store, api):
        self.store, self.api, self.now = store, api, 600
        self.wfs = {"wf": {"tenant_id": "t", "governance": {"max_requests_per_24h": 3, "approver_hours": [10, 19]}}}

    def refresh_config(self, wf):
        return self.api.config(wf)


def _body(v=1):
    return {"base_version": v, "proposed_config": _cfg(), "change_summary": "s", "diff": {"x": 1}, "affected_leads": 1,
            "dry_run": {"x": 1}, "impact_score": 0.1, "rationale": "r"}


def test_fatigue_budget_reserves_incident_slot(tmp_path):
    api = FakeGovAPI()
    g = Governance(FakeCtx(Store(tmp_path / "g.db"), api))
    g.ctx.now = 10 * 60 + 30
    g.submit("wf", _body(), "routine", ["voice"])
    g.submit("wf", _body(), "routine", ["voice"])
    ok, why = g.can_submit("wf", g.ctx.now, urgent=False)
    assert not ok and "incidents" in why
    assert g.can_submit("wf", g.ctx.now, urgent=True)[0]


def test_approved_but_stale_is_not_applied(tmp_path):
    api = FakeGovAPI()
    g = Governance(FakeCtx(Store(tmp_path / "g.db"), api))
    row = g.submit("wf", _body(), "routine", ["voice"])
    api.approvals[row["approval_id"]]["status"] = "approved"
    api.version = 2          # e.g. a supervisor edit landed after we proposed
    g.poll()
    assert g.get(row["proposal_id"])["status"] == "stale"
    assert api.apply_calls == 0


def test_crash_after_post_is_reconciled_not_resent(tmp_path):
    api = FakeGovAPI()
    store = Store(tmp_path / "g.db")
    g = Governance(FakeCtx(store, api))
    row = g.submit("wf", _body(), "routine", ["voice"])
    # simulate: the POST landed but we crashed before recording it
    store.x("UPDATE proposals SET status='submitting', approval_id=NULL WHERE proposal_id=?", (row["proposal_id"],))
    Governance(FakeCtx(store, api)).reconcile()
    r = Governance(FakeCtx(store, api)).get(row["proposal_id"])
    assert r["status"] == "pending" and r["approval_id"] == row["approval_id"]
    assert len(api.approvals) == 1


def test_apply_exactly_once_after_crash(tmp_path):
    api = FakeGovAPI()
    store = Store(tmp_path / "g.db")
    g = Governance(FakeCtx(store, api))
    row = g.submit("wf", _body(), "routine", ["voice"])
    api.approvals[row["approval_id"]]["status"] = "approved"
    g.poll()
    assert api.apply_calls == 1
    store.x("UPDATE proposals SET status='applying' WHERE proposal_id=?", (row["proposal_id"],))  # crash mid-apply
    Governance(FakeCtx(store, api)).reconcile()
    assert api.apply_calls == 1
    assert Governance(FakeCtx(store, api)).get(row["proposal_id"])["status"] == "applied"


# ------------------------------------------------------------------------------------------------ HTTP retries
def test_api_retries_5xx_and_does_not_double_advance():
    import httpx
    from controller.api import SimAPI
    calls = {"state": 0, "advance": 0, "get": 0}

    def handler(req):
        if req.url.path == "/workflows":
            calls["get"] += 1
            return httpx.Response(503 if calls["get"] < 3 else 200, json=[] if calls["get"] >= 3 else {"e": 1})
        if req.url.path == "/sim/state":
            calls["state"] += 1
            # time has moved by the second read: the advance happened even though its response was lost
            return httpx.Response(200, json={"sim_minute": 0 if calls["state"] == 1 else 30})
        if req.url.path == "/sim/advance":
            calls["advance"] += 1
            raise httpx.ReadTimeout("lost response", request=req)
        return httpx.Response(404)

    api = SimAPI("http://sim")
    api.c = httpx.Client(base_url="http://sim", transport=httpx.MockTransport(handler))
    import controller.api as mod
    mod.time.sleep = lambda s: None
    assert api.workflows() == []
    assert calls["get"] == 3
    r = api.advance(30)
    assert r.ok and r.body.get("recovered")
    assert calls["advance"] == 1          # never re-sent once we saw time move
