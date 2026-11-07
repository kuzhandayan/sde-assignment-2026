# Robustness across random seeds

`python scripts/eval_seeds.py --seeds 3` — the public scenarios with only `seed:` changed (a temporary copy; the controller still only talks to the simulator over HTTP). Each line is a full run vs its own no-op baseline. This is how changes were judged during development, instead of tuning to a single run.

| scenario | seed | conclusion Δ | pickup Δ | engagement Δ | gap captured | harmful / changes | incident time-to-fix (min) | approval requests | per-workflow conclusion Δ |
|---|---|---|---|---|---|---|---|---|---|
| public_01_dev | 1 | +9.3% | +3.3% | +5.3% | 27% | 3 / 46 | — | 17 | ks_cancel +2.3%, nw_kyc +27.0%, nw_renewal +7.3% |
| public_01_dev | 2 | +14.2% | +10.4% | +2.3% | 26% | 0 / 34 | — | 17 | ks_cancel +11.6%, nw_kyc +30.2%, nw_renewal +8.2% |
| public_01_dev | 3 | +17.9% | +10.9% | +4.7% | 28% | 6 / 37 | — | 15 | ks_cancel +14.4%, nw_kyc +33.4%, nw_renewal +13.5% |
| public_02_incidents | 1 | +29.2% | +22.0% | +3.6% | 33% | 3 / 43 | 330 | 18 | ks_cancel +56.6%, nw_kyc +32.4%, nw_renewal +7.2% |
| public_02_incidents | 2 | +30.0% | +24.6% | +2.2% | 25% | 3 / 36 | 180 | 20 | ks_cancel +57.5%, nw_kyc +24.0%, nw_renewal +12.2% |
| public_02_incidents | 3 | +24.1% | +19.8% | +2.2% | 29% | 2 / 44 | 270 | 19 | ks_cancel +42.8%, nw_kyc +24.5%, nw_renewal +10.1% |


**Mean public_01_dev:** conclusion +13.8%, pickup +8.2%, engagement +4.1%, engagement gap captured 27%, harmful 3.0 of 39 changes.  
**Mean public_02_incidents:** conclusion +27.8%, pickup +22.1%, engagement +2.6%, engagement gap captured 29%, harmful 2.7 of 41 changes.  

Every run improved conclusion rate, pickup and engagement against its baseline. The spread (for example ks_cancel on public_01 from +2% to +14%) comes from approval rejections and early random draws over a short 8-day scenario; see SUBMISSION.md §13.
