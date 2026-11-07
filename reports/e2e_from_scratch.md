# End-to-end verification from scratch

Run on Linux x86_64, 2 CPU, 2026-11-07T15:43Z. Fresh clone of commit `82c8995`, fresh virtualenv.

| step | result | wall | last line of output |
|---|---|---|---|
| git clone (committed files only) | PASS | 0s |  |
| fresh virtualenv + pip install -r requirements.txt | PASS | 5s | deps ok |
| unit + simulator tests (pytest) | PASS | 2s | 19 passed in 2.38s |
| controller never reads simulator internals | PASS | 0s | no access to sim/, runs/ or scenario files |
| public_01 end to end via run.sh | PASS | 41s | / ALL / 0.436 / +16.1% / 0.272 / +9.8% / 0.563 / +4.6% / 37% / 139 (112) / |
| public_02 end to end via run.sh | PASS | 58s |     "mttr_minutes": 270, |
| audit: why did ks_cancel change (public_02) | PASS | 0s | **Who:** auto-applied by the controller under the signed policy (auto_apply allowed_dims=['schedule', 'caller_id', 'welcome_message', 'voice |
| audit: what a customer heard | PASS | 0s | - D-13 12:48  ks_cancel:l00000000  welcome=W1 voice=V1 caller_id=D1 prompt=P1  cohort=default  config v1 (that cohort's  |
| supervisor view serves HTML + JSON (token on) | PASS | 4s | no token -> 401, token -> 200, loop chunks 251 |
| crash-recovery test (injected + random kills) | PASS | 57s | **Result: PASS** |
| edge cases (9 scenarios) | PASS | 100s | **9/9 passed.** |
| docker build controller (--no-cache, base localpython:3.13) | FAIL | 14s | ERROR: failed to build: failed to solve: process "/bin/sh -c pip install --no-cache-dir -r requirements.txt" did not complete successfully:  |
| docker build simulator (--no-cache, base localpython:3.13) | FAIL | 1s | ERROR: failed to build: failed to solve: process "/bin/sh -c pip install --no-cache-dir -r requirements.txt" did not complete successfully:  |
| docker compose: sim + controller run public_01 to the end | FAIL | 1s |  |
| run.sh USE_DOCKER=1 against a host simulator (public_02) | FAIL | 9s |  |
| docker: kill controller container mid-run, restart, finish | FAIL | 24s | Error response from daemon: No such container: e2e_ctl |

**11 passed, 5 failed.** Logs for each step are next to this report in `/tmp/e2e_from_scratch`.
