# Requirement tracker — Round 2 (Agentic Universe, AI Systems Engineer)

Every requirement from `README.md`, the stakeholder memos and `SUBMISSION_TEMPLATE.md`, with its status and
where to find the evidence.

- ✅ done and verified
- 🟡 partial (scope choice, explained in SUBMISSION.md §2)
- ❌ cut on purpose
- 👤 **you need to do this** before submitting

**Deadline:** Monday 9 November 2026 · **Submit at:** https://forms.cloud.microsoft/r/9q1p6YzBVy

---

## A. Things only you can do 👤

| # | Task | Status |
|---|---|---|
| A1 | Fill in **Hours actually spent** in `SUBMISSION.md` | ✅ done: about 8 hours, AI-assisted (allowed by the brief, README line 174). Update it if you spend more time before submitting |
| A2 | Read `SUBMISSION.md` fully and rewrite any stakeholder reply (§3) in your own words if you want | 👤 to do |
| A3 | Push to GitHub, **public** (the form asks for a publicly accessible link), commit history as-is | ✅ done 8 Nov: https://github.com/kuzhandayan/sde-assignment-2026 |
| A4 | Verify Docker once with the real base image (`docker compose up` on the Mac) | ✅ done 8 Nov — built from `python:3.12-slim`, sim healthy, controller ran D0–D7 and exited 0 |
| A5 | Run it once on your Mac: `docker compose up --build` (tests + public_01 + public_02 + supervisor view) | ✅ done 8 Nov |
| A6 | Optional: record a ≤ 5-min walkthrough video (show `why`, the supervisor view, the crash test) | 👤 optional |
| A7 | Check whether you submitted Round 1 — if not, the email says both rounds are needed | 👤 check |
| A8 | Prepare for the 60-min review: be able to explain one decision live from the audit store (`python -m controller why ...`), say what breaks if a constraint changes, and defend each cut | 👤 prepare |

## B. Floor (mandatory) — README §6

| # | Requirement | Status | Evidence |
|---|---|---|---|
| B1 | Controller runs public_01 end to end, no manual steps | ✅ | `./run.sh <SIM_URL>`; `reports/public_01.md` |
| B2 | Controller runs public_02 end to end, no manual steps | ✅ | `reports/public_02.md` |
| B3 | Audit trail (C12) | ✅ | `decisions` table, `python -m controller why`, SUBMISSION §10 |
| B4 | Never breaks the constraints (section C) | ✅ | 0 auto-apply refusals, 0 apply conflicts, 0 lapses, guardrails within limits in all runs |
| B5 | `SUBMISSION.md` complete (every template heading) | ✅ (except A1) | `SUBMISSION.md` §0–§14 |

## C. Non-negotiable constraints — README §5

| # | Constraint | Status | How it's enforced |
|---|---|---|---|
| C-1 | Governance boundary absolute; supervisor edits never overwritten silently | ✅ | Only `governance.py` writes config; supervisor dims frozen 24h + sticky (approval-only after); requests that touch them start with "CHANGES A SUPERVISOR EDIT" |
| C-2 | Business owns whether/when to call (no cadence/window/capacity changes) | ✅ | Hour weights never 0 (no capacity left unused), no pause-dialling lever |
| C-3 | Pickup and engagement separate; optimise primary, respect guardrail | ✅ | Pickup guardrail check + rollback; engagement guardrail softens call-time weights; KPIs never blended |
| C-4 | Winner selection statistical and deterministic; LLM never decides | ✅ | Seeded P(best) + Holm; LLM only proposes prompts in incidents, validation + live data decide |
| C-5 | Act on populations, not anecdotes | ✅ | Every detector has a minimum n and a significance test (settings.py) |
| C-6 | Every decision auditable from our own store | ✅ | `decisions`, `proposals`, `world_events`, `calls_heard` |
| C-7 | Credits finite; don't run out mid-incident | ✅ | Known-good rollback first (no LLM), 20-credit reserve for incidents; 5 credits used on public_02 |
| C-8 | Crash safety: resume, no double-apply, no lost approval, no forgotten learning | ✅ | `reports/crash_recovery.md` — 9 starts, all checks PASS |
| C-9 | Controller only knows what the HTTP API says (no `runs/`, no `sim` import, no scenario parsing) | ✅ | `grep -rn "import sim\|runs/\|scenarios" controller/` finds nothing |
| C-10 | `./run.sh <SIM_URL>` starts the controller and runs to the end | ✅ | `run.sh` (Docker when available, else Python 3.10+; `USE_DOCKER=0/1` to force) |

## D. Capabilities C1–C15 — README §6 (choose; don't do everything)

| # | Capability | Status | Evidence |
|---|---|---|---|
| C1 | Event ingestion at load scale, backlog-safe, idempotent, restartable | ✅ | `ingest.py`; 145–160k ev/s; exactly-once test |
| C2 | One shared cohort object | ✅ | `cohorts.py` / `cohorts` table |
| C3 | Bootstrapping from history | ✅ | Call-time cells, caller-ID status, hallucination + engagement baselines from history |
| C4 | Call-time optimisation | 🟡 | Per cohort ✅, per person ❌ (data too thin — SUBMISSION §5) |
| C5 | Caller-ID health: detect, rotate, explore safely | ✅ | `policies/callerid.py` |
| C6 | Variant experiments (welcome × voice), sample sizes, multiple comparisons | ✅ | `policies/experiments.py` |
| C7 | Winner promotion, decay detection, rollback | ✅ | decay rollback seen in public_01/02 decisions |
| C8 | Hallucination incident: detect → LLM → validate → propose → verify | ✅ | public_02: fixed in 300 min, verified |
| C9 | Governance client (lifecycle, batching, hours, expiry/lapse, stale re-proposal, auto-apply) | ✅ | `governance.py`, `planner.py` |
| C10 | Honest impact, affected leads, dry runs | ✅ | defined in SUBMISSION §6 |
| C11 | Consolidated supervisor view | 🟡 | live page per tenant at http://localhost:8800 (auto-refresh); read-only, no approve buttons |
| C12 | Queryable decision/audit store | ✅ | `why`, `heard`, SQL |
| C13 | Crash recovery demonstrated | ✅ | `scripts/crash_test.py`, `reports/crash_recovery.md` |
| C14 | Observability of the loop | 🟡 | `metrics`, `alerts`, `/api/loop` (no Prometheus) |
| C15 | Fair allocation of credits / approver attention across tenants | ❌ | cut — SUBMISSION §2 |

## E. Deliverables — README §8

| # | Deliverable | Status | Where |
|---|---|---|---|
| E1 | Controller with `run.sh` | ✅ | `controller/`, `run.sh` |
| E2 | `SUBMISSION.md` from the template | ✅ (A1, A2) | `SUBMISSION.md` |
| E3 | `reports/`: grade for public_01 and public_02 | ✅ | `reports/public_01.md`, `reports/public_02.md` |
| E4 | `reports/`: load-test numbers for public_03 | ✅ | `reports/public_03_load.md`, `reports/public_03_grade.md` |
| E5 | Crash-recovery evidence (script or log) | ✅ | `scripts/crash_test.py`, `reports/crash_recovery.md` |
| E6 | Commit history that shows thinking (small honest commits) | ✅ | `git log` — one commit per step |
| E7 | Optional walkthrough video ≤ 5 min | 👤 optional | — |
| E8 | Private repo shared with the form's email | 👤 A3 | — |

## F. Stakeholder memos — README §7 (accept / push back / wrong claims / reply ≤ 120 words)

| # | Memo | Status | Wrong claim found |
|---|---|---|---|
| F1 | 01 Sales | ✅ SUBMISSION §3 | "Kestrel auto-apply for everything" (no: prompt/cohorts excluded, max_shift 0.2); "Northwind OK with auto-apply on KYC" (no: disabled) |
| F2 | 02 Compliance | ✅ | "timing & caller-ID covered by policy" — true for renewal only, not KYC |
| F3 | 03 SRE | ✅ | — (all non-negotiables met: kill test, idempotency, actionable alerts, < 10 min/day) |
| F4 | 04 Kestrel ops supervisor | ✅ | "2 requests/day, not before 11" is stricter than policy (4/24h from 10) — honoured anyway |
| F5 | 05 Product | ✅ | per-person call time pushed back with data (5 dials / person) |
| F6 | 06 CTO | ✅ | summary of choices + wrong claims |

## G. SRE / performance asks

| # | Ask | Status | Number |
|---|---|---|---|
| G1 | One sim day of public_03 in < 10 wall-minutes on 4 vCPU / 8 GB | ✅ | 22–49 s on 2 vCPU |
| G2 | Where it breaks at 10× | ✅ | `reports/public_03_load.md` |
| G3 | Ingest throughput, decision lag, memory | ✅ | 145–160k ev/s · p99 1.8 s · 748 MB peak |
| G4 | No new stateful infrastructure | ✅ | SQLite file only |
| G5 | Loop health without reading logs | ✅ | `/api/loop`, `metrics` table |

## H. Engineering quality

| # | Item | Status | Where |
|---|---|---|---|
| H1 | Unit tests where they matter | ✅ | `tests/test_controller.py` (13) + simulator tests (6) — all pass |
| H2 | Docs a new engineer can run/debug/extend from | ✅ | `README_CONTROLLER.md` (run, inspect, runbook, extend) |
| H3 | Robustness across seeds (not tuned to one run) | ✅ | `scripts/eval_seeds.py`, `reports/seed_robustness.md` |
| H4 | Docker | ✅ | one image (`Dockerfile`); `docker compose up` runs tests + public_01 + public_02 and serves the view; verified with the real `python:3.12-slim` on macOS (A4) |
| H6 | Edge cases end to end | ✅ | `scripts/edge_cases.py` 9/9 (`reports/edge_cases.md`) |
| H7 | Full from-scratch verification | ✅ | fresh clone, clean environment, `--no-cache` build: every test, scenario, audit query and Docker path passed (SUBMISSION.md §9) |
| H9 | Live supervisor view and hot reload | ✅ | `docker compose up` shows http://localhost:8800 from the start (refreshes every 10 s, follows the run in progress); saving code in `controller/` restarts the run with the new code |
| H8 | One command, Docker only (no local Python/venv) | ✅ | `docker compose up --build`; `docker compose run --rm dev <cmd>` for single commands; `./run.sh` uses Docker when available, else Python 3.10+; runs never write to `reports/` |
| H5 | Authentication | ✅ (by decision) | Not required by the brief. View is read-only, localhost-bound, optional `VIEW_TOKEN` bearer token; production sits behind SSO/gateway |
