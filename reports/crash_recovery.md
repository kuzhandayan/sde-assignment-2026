# Crash-recovery test

Scenario `scenarios/public_02_incidents.yaml`, 9 controller starts on one SQLite file.
Injected hard exits (like kill -9) right after each kind of POST/PUT is sent but before its result is recorded, and in the middle of an ingest transaction; plus random SIGKILLs.

## Timeline

- start 1: [fault-injection] hard exit at after_auto_put (sim at 2027-01-04T08:00:00+05:30)
- start 2: [fault-injection] hard exit at mid_chunk (sim at 2027-01-04T08:30:00+05:30)
- start 3: [fault-injection] hard exit at after_approval_post (sim at 2027-01-04T10:00:00+05:30)
- start 4: [fault-injection] hard exit at after_apply_post (sim at 2027-01-04T13:00:00+05:30)
- start 5: SIGKILL after 12.6s wall, sim at 2027-01-08T08:00:00+05:30
- start 6: SIGKILL after 9.9s wall, sim at 2027-01-09T19:00:00+05:30
- start 7: SIGKILL after 4.9s wall, sim at 2027-01-10T16:00:00+05:30
- start 8: SIGKILL after 12.1s wall, sim at 2027-01-12T15:00:00+05:30
- start 9: exited 0 after 10.6s

## Checks

- PASS — scenario finished: 2027-01-14T00:00:00+05:30
- PASS — every simulator approval is in our store: 23 approvals, missing []
- PASS — our proposal states agree with the simulator: mismatches []
- PASS — no approval applied twice: 17 applied, duplicates []
- PASS — no apply conflicts / lapses: apply_conflict=0, lapsed=0
- PASS — every applied controller change is 'applied' in our store: lost []
- PASS — ingestion exactly-once (event count): ours 324389 vs simulator 324389
- PASS — connected-call aggregates match a recount of raw chunks: recount {'nw_renewal': 23849, 'ks_cancel': 28451, 'nw_kyc': 12876} vs store {'ks_cancel': 28451, 'nw_kyc': 12876, 'nw_renewal': 23849}

**Result: PASS**

Grade of the crashed run (same metrics as a normal run):

```
# Grade report — public_02_incidents

## Outcomes vs baseline (no-op controller)

| workflow | conclusion rate | Δ | pickup | Δ | engagement | Δ | engagement gap captured | hallucinated calls (base) |
|---|---|---|---|---|---|---|---|---|
| ks_cancel | 0.376 | +54.2% | 0.254 | +39.0% | 0.505 | +6.9% | 46% | 87 (310) |
| nw_kyc | 0.462 | +20.3% | 0.289 | +16.6% | 0.607 | +1.2% | 11% | 37 (38) |
| nw_renewal | 0.487 | +13.2% | 0.291 | +10.6% | 0.557 | +1.8% | 3% | 62 (58) |
| ALL | 0.431 | +28.5% | 0.273 | +22.6% | 0.545 | +2.7% | 29% | 186 (406) |
```