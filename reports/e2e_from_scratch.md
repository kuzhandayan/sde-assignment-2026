# End-to-end verification from scratch

Run on Linux x86_64, 2 CPU, 2026-11-07T16:07Z. Fresh clone of commit `709d21c`, fresh virtualenv.

| step | result | wall | last line of output |
|---|---|---|---|
| git clone (committed files only) | PASS | 0s |  |
| fresh virtualenv + pip install -r requirements.txt | PASS | 6s | deps ok |
| unit + simulator tests (pytest) | PASS | 2s | 19 passed in 2.20s |
| controller never reads simulator internals | PASS | 0s | no access to sim/, runs/ or scenario files |
| public_01 end to end via run.sh | PASS | 46s | / ALL / 0.432 / +15.2% / 0.274 / +10.6% / 0.554 / +2.9% / 27% / 139 (112) / |
| public_02 end to end via run.sh | PASS | 64s |     "mttr_minutes": 300, |
| audit: why did ks_cancel change (public_02) | PASS | 0s | **Who:** auto-applied by the controller under the signed policy (auto_apply allowed_dims=['schedule', 'caller_id', 'welcome_message', 'voice |
| audit: what a customer heard | PASS | 0s | - D-13 12:48  ks_cancel:l00000000  welcome=W1 voice=V1 caller_id=D1 prompt=P1  cohort=default  config v1 (that cohort's  |
| supervisor view serves HTML + JSON (token on) | PASS | 4s | no token -> 401, token -> 200, loop chunks 251 |
| crash-recovery test (injected + random kills) | PASS | 59s | **Result: PASS** |
| edge cases (9 scenarios) | PASS | 100s | **9/9 passed.** |
| docker build controller (--no-cache, base localpython:3.13) | PASS | 2s | sha256:484c47fc1d24643c0f45e33e8fd635a563a72cfc91e6917f7ac961434b31d763 |
| docker build simulator (--no-cache, base localpython:3.13) | PASS | 2s | sha256:8f47cef9c9b0f93d3e8d128a0e103f18cf9daa860ccfd2dbb972d2759aacce7e |
| docker compose: sim + controller run public_01 to the end | PASS | 52s | / ALL / 0.432 / +15.2% / 0.274 / +10.6% / 0.554 / +2.9% / 27% / 139 (112) / |
| run.sh USE_DOCKER=1 against a host simulator (public_02) | PASS | 69s | / ALL / 0.432 / +28.7% / 0.277 / +24.0% / 0.540 / +1.8% / 26% / 188 (406) / |
| docker: kill controller container mid-run, restart, finish | PASS | 54s | restarted ok; decisions: 1 restart(s) recorded |

**16 passed, 0 failed.** Logs for each step are next to this report in `/tmp/e2e_from_scratch`.
