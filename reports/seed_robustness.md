# Robustness across random seeds

`python scripts/eval_seeds.py --seeds 3` — the public scenarios with only `seed:` changed (a temporary copy; the controller still only talks to the simulator over HTTP). Each line is a full run against its own no-op baseline. This is how changes were judged during development, instead of tuning to a single run.

| scenario | seed | conclusion Δ | pickup Δ | engagement Δ | gap captured | harmful / changes | incident time-to-fix (min) | approval requests | per-workflow conclusion Δ |
|---|---|---|---|---|---|---|---|---|---|
| public_01_dev | 1 | +16.3% | +9.2% | +4.8% | 28% | 4 / 38 | — | 16 | ks_cancel +13.5%, nw_kyc +30.4%, nw_renewal +11.6% |
| public_01_dev | 2 | +18.7% | +11.2% | +4.8% | 33% | 0 / 30 | — | 19 | ks_cancel +16.9%, nw_kyc +29.5%, nw_renewal +14.6% |
| public_01_dev | 3 | +14.7% | +7.1% | +6.0% | 37% | 0 / 42 | — | 16 | ks_cancel +14.8%, nw_kyc +26.3%, nw_renewal +8.4% |
| public_02_incidents | 1 | +29.0% | +23.2% | +2.9% | 27% | 2 / 37 | 360 | 22 | ks_cancel +56.5%, nw_kyc +25.3%, nw_renewal +10.7% |
| public_02_incidents | 2 | +27.3% | +21.4% | +2.8% | 31% | 1 / 40 | 450 | 19 | ks_cancel +56.6%, nw_kyc +19.8%, nw_renewal +8.8% |
| public_02_incidents | 3 | +24.5% | +20.1% | +1.9% | 21% | 4 / 46 | 330 | 22 | ks_cancel +44.6%, nw_kyc +26.7%, nw_renewal +8.6% |

**Mean public_01_dev:** conclusion +16.5%, pickup +9.2%, engagement +5.2%, engagement gap captured 33%, harmful 1.3 of 37 changes.  
**Mean public_02_incidents:** conclusion +27.0%, pickup +21.6%, engagement +2.5%, engagement gap captured 26%, harmful 2.3 of 41 changes.  

Every run improved conclusion rate, pickup and engagement against its baseline. The spread between seeds comes from approval rejections and early random draws over a short scenario; see SUBMISSION.md §13.
