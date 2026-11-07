# Controller — run, debug, extend

This is the engineer's guide to the controller in `controller/`. The assignment brief is in
[`README.md`](README.md). The design write-up is in [`SUBMISSION.md`](SUBMISSION.md). The requirement tracker
is [`TODO.md`](TODO.md).

## 1. Run it

You only need **Docker**. Docker brings Python and every package, so there's no venv or local Python setup.

```bash
# run a whole scenario: simulator + controller (Ctrl+C after "controller-1 exited with code 0")
SCENARIO=public_02_incidents docker compose up --build sim controller
docker compose down

# everything else runs in the `dev` container (the repo mounted into the controller image)
docker compose run --rm dev                                       # unit tests
docker compose run --rm dev scripts/run_scenario.sh scenarios/public_02_incidents.yaml public_02 8702
                                                                  # sim + controller + grade, live progress
```

The assignment contract is `./run.sh <SIM_URL>`. It runs the controller in Docker when Docker is available and
falls back to local Python 3.10+ (`pip install -r requirements.txt`) on a machine without Docker.

| env var | default | meaning |
|---|---|---|
| `CONTROLLER_DB` | `state/controller.db` | the controller's only state. Same file = resume after a crash. **New simulator run = new file.** |
| `USE_DOCKER` | auto | `1` forces Docker, `0` forces local Python |
| `STORE_CALLS` | `1` | keep what every customer heard on connected calls (compliance query). `0` saves disk at scale |
| `VIEW_TOKEN` | unset | if set, the supervisor view requires `Authorization: Bearer <token>` |
| `CONTROLLER_WAIT_S` | `600` | how long to wait for the simulator before exiting with an error |
| `BASE_IMAGE` | `python:3.12-slim` | Docker base image (override for offline builds) |

Safety rails at start-up:
- A second controller on the same DB is refused (file lock).
- A DB from a different simulator run is refused, because a simulator restart is a new world.

Note: the simulator draws its world with numpy's random generator, so a different numpy version builds a slightly
different world. Reports regenerated on another machine can differ in detail from the committed ones.

## 2. Look at what it did

```bash
# why did workflow X change at time T, who approved it, what happened next
docker compose run --rm dev python -m controller why --db state/public_02.db --workflow ks_cancel --at "D3 16:30"
# what a customer heard on each call, and why that variant was live (IRDAI question)
docker compose run --rm dev python -m controller heard --db state/public_02.db --person ks_cancel:p0001234
# supervisor view of the last `docker compose up` run: one screen per tenant + loop health JSON
SCENARIO=public_02_incidents docker compose --profile view up view   # http://127.0.0.1:8800/tenant/kestrel_finance
```

Everything can also be queried directly. The `decisions` table is the plain-language audit log:

```sql
SELECT minute/1440 AS day, (minute%1440)/60 AS hour, workflow_id, kind, summary
FROM decisions WHERE workflow_id='ks_cancel' AND kind LIKE 'incident%' ORDER BY id;
```

## 3. How it works (one paragraph per file)

```
controller/
  loop.py        main loop: ingest -> refresh configs -> poll approvals -> plan each workflow -> metrics -> advance
  api.py         HTTP client. Retries GETs and idempotent POSTs; never blindly retries /sim/advance or credit spend
  store.py       SQLite schema (WAL). One transaction per unit of work
  ingest.py      chunk -> aggregates, committed with the chunk number in one transaction (exactly-once)
  data.py        read models: post-stratified arm engagement, pickup by hour/caller ID, QA windows, active leads
  cohorts.py     the shared cohort registry + config helpers (changed_dims, max_shift, first-match)
  stats.py       z-tests, Wilson, exact binomial, Holm, seeded P(best)
  planner.py     composes ONE desired config per workflow; splits it into auto-apply part + approval request
  governance.py  proposal state machine, fatigue budget, approver-hours timing, apply, crash reconcile
  policies/
    schedule.py    call-time cells learned from history; hour weights; pickup + engagement guardrails
    callerid.py    caller-ID health: probe / degraded / pulled / rest / re-probe
    prompts.py     hallucination incidents: detect -> rollback candidate -> validate -> propose -> verify
    experiments.py welcome x voice: P(best) allocation, harm suspension, Holm promotion, decay rollback, segments
  audit.py       `why` and `heard`
  view.py        supervisor view + loop health (FastAPI, read-only)
  faults.py      crash injection for the recovery test (inactive unless CRASH_POINTS is set)
  settings.py    every threshold, with the reason for its value
```

Each 30-minute step does three things per workflow, in priority order:

1. Hallucination incident.
2. Caller ID gone bad.
3. Routine optimisation.

Routine changes become **one batched request a day**, unless something happened (a promotion, a rollback, a
new segment or a harm stop). Changes the policy allows are auto-applied, but never while an approval is in
flight and never on a dim a supervisor edited.

## 4. On-call runbook

Alerts live in the `alerts` table and in `/api/loop` (`alerts_page`). Severity `page` means act now. Severity
`ticket` means it can wait until morning.

| alert | severity | what to look at |
|---|---|---|
| `hallucination spike on prompt X` | page | `why --at <time>` on that workflow; check the incident proposal in `/tenant/...` is pending with the approver. Nothing to do if it is |
| `no validated fix for hallucination spike` | page | every candidate prompt failed validation. A human picks a prompt; the validation results are in `incidents.detail` |
| `hallucinations still high after fix` | page | the rollback target is also bad, or the detector baseline is wrong. Compare `qa_by_prompt` over the last day |
| `out of credits during hallucination incident` | page | top up credits. Routine work stops spending at `CREDIT_RESERVE`, so this means a real incident burned the budget |
| `N approved change(s) lapsed in 24h` | page | the loop is not polling in time: check `decision_lag_s` in `metrics`, and whether the process is restarting in a loop |
| `planner error` | page | stack trace in the controller log. Other workflows keep running |
| `credits low` | ticket (page during an incident) | plan a top-up |
| `proposal rejected for evidence` | ticket | a request was rejected for missing or failed validation evidence. That is a bug |
| `engagement lower after prompt fix` | ticket | the fix is safe but loses engagement (the "verbatim script" case). Consider another validated prompt |

What does **not** page: a single rejection (approvers decline about 10% by judgement), an expired request
(re-planned automatically), a supervisor edit (respected automatically), or a caller ID pulled (handled
automatically and shown in the view).

**Restart is always safe.** Kill it, then run the same command with the same `CONTROLLER_DB`. On start-up it
does three things:

1. Re-reads uncommitted chunks.
2. Reconciles every in-flight proposal against `/approvals` and the config history.
3. Carries on.

`scripts/crash_test.py` proves this. See [`reports/crash_recovery.md`](reports/crash_recovery.md).

## 5. Test

```bash
docker compose run --rm dev                                        # 13 controller unit tests + simulator tests (≈3 s)
docker compose run --rm dev python scripts/crash_test.py --kills 4 # kill/restart test against a live simulator (≈2 min)
docker compose run --rm dev python scripts/edge_cases.py           # 9 end-to-end edge cases (≈3 min)
docker compose run --rm dev python scripts/eval_seeds.py --seeds 3 # robustness across random seeds (≈6 min)
scripts/e2e_from_scratch.sh        # CI-style: fresh clone + fresh venv + everything + Docker build (Linux, ≈20 min)
```

## 6. Extend it

- **A new optimisation lever:** write a policy in `policies/` that reads evidence through `data.Evidence` and
  returns a target for its dims. Add one block in `Planner.build_target` that writes the dim into `cfg` and
  fills `info` (summary, why, dry_run, impact_parts). Governance, auto-apply limits, batching, freezes and
  the audit trail then apply automatically.
- **A new tenant preference** that is stricter than policy: add it to `settings.TENANT_PREFS`.
- **A new alert:** call `store.alert(minute, "page"|"ticket", wf, summary, action)`. The action text must tell
  the on-call engineer what to look at.
- **Never** read `runs/` or scenario files from the controller, and never import `sim`. The controller may
  only know what the HTTP API tells it.
