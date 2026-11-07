# Load test — public_03_load (12 workflows, 5 days, ~850k events/day)

Measured on the development box: **2 vCPU / 8 GB** (the grading box has 4 vCPU). The simulator and the
controller ran on the same machine, so every wall-clock number below includes the simulator generating the
world. Raw grade output: [`public_03_grade.md`](public_03_grade.md).

## Throughput and lag

| metric | value | how measured |
|---|---|---|
| history ingested at start-up (7 days) | 5,536,955 events in 34.9 s of ingest time (48.9 s wall incl. HTTP) | `chunks_done.wall_s` |
| live events ingested (5 days) | 4,200,213 events, 125 chunks | `chunks_done` |
| ingest throughput | **145k–160k events/s** (single thread, stdlib `json`) | events / `wall_s` |
| wall-clock per simulated day | **22–49 s** (incl. simulator) | controller log timestamps at each `D? 00:00` |
| SRE target (stakeholders/03) | < 10 min per simulated day | **met with >12x headroom** |
| decision lag per 30-min step (ingest + reconcile + 12 planners) | p50 0.46 s · p95 1.51 s · p99 1.79 s · max 2.0 s | `metrics.decision_lag_s` |
| peak RSS (controller) | 748 MB (during the 5.5M-event history load) | `getrusage` → `metrics.rss_mb` |
| SQLite file after the run | 379 MB (2.0M heard-call rows, 354k pickup aggregate rows, 74k engagement aggregate rows) | file size |
| credits used | 0 of 400 (no hallucination incident in this scenario) | grader |

## Outcomes (vs no-op baseline)

| | conclusion rate | pickup | engagement |
|---|---|---|---|
| ALL 12 workflows | **+24.7%** | +13.2% | +7.6% |
| worst workflow (tide_cancel_2) | +17.6% | | |

100 config changes applied: **44 beneficial, 55 neutral, 1 harmful** (an early exploration step on
tide_cancel_2). 55 approval requests (48 approved, 5 judgement-call rejections, 0 expired), 54 auto-applies,
**0 apply conflicts, 0 lapses**, peak 2 requests per 24h per workflow (limit 2–4).

Hallucinated calls went from 4,650 to 5,308: no prompt changed (the flag rate per connected call is the
baseline rate); there are simply ~13% more connected calls because pickup went up.

## Where it breaks at 10x (≈ 8.5M events/day, ~120 workflows)

In order of what fails first:

1. **`calls_heard` (what each customer heard).** 2.0M rows in 5 days here, so ~20M per 5 days at 10x and
   ~400M per 100 days. The SQLite file and its person index become the bottleneck for both write
   amplification and backups. Fix: it duplicates the platform's own call log, so in production keep only
   `(call_id, config_version, cohort_id)` in Postgres partitioned by day, or point the audit query at the
   warehouse. Can be switched off today with `STORE_CALLS=0`.
2. **Single writer.** SQLite serialises all writes. At 10x the per-step write is ~10x larger (still small:
   aggregates, not dials), but one slow workflow's planner delays every other workflow's step. Fix: shard.
3. **Single-threaded ingest** at ~150k events/s ≈ 57 s of CPU per 10x day. Not the first thing to break,
   but it's on the critical path of every step. Fix: parse chunks in a process pool (orjson would also give
   ~3x), or consume a partitioned stream.
4. **Planner reviews** re-read 10 days of engagement aggregates per workflow. Cheap today (tens of ms);
   linear in workflows × cohorts × arms. Fix: incremental per-arm sufficient statistics.

**How I'd partition:** shard by `workflow_id` (every decision is per workflow; tenants only share approver
attention and credits). N controller workers, each owning a hash range of workflows, consuming an event
stream keyed by `workflow_id`, with state in the platform's Postgres (one schema, row-level ownership by
workflow, an advisory lock per workflow so two workers can never plan the same workflow). Credits and
approver attention are the only cross-workflow resources; they'd move to a small allocator service with a
per-tenant budget (C15, not built).
