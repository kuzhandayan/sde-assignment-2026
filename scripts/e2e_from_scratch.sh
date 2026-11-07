#!/usr/bin/env bash
# Full from-scratch verification: fresh clone of the COMMITTED repo, fresh virtualenv, every test, every
# scenario, crash test, edge cases, and the Docker path built with --no-cache. Writes reports/e2e_from_scratch.md
# in the clone and copies it back here.
#
#   scripts/e2e_from_scratch.sh                     # Docker base image python:3.12-slim (needs Docker Hub)
#   BASE_IMAGE=localpython:3.13 scripts/e2e_from_scratch.sh   # any local image with python3 on PATH
#   SKIP_DOCKER=1 scripts/e2e_from_scratch.sh
set -uo pipefail
SRC="$(cd "$(dirname "$0")/.." && pwd)"
W="${E2E_DIR:-/tmp/e2e_from_scratch}"
rm -rf "$W"; mkdir -p "$W"
REPORT="$W/report.md"
pass=0; fail=0
step() {  # step "name" command...
  local name="$1"; shift
  local t0=$(date +%s)
  if "$@" > "$W/step.log" 2>&1; then r=PASS; pass=$((pass+1)); else r=FAIL; fail=$((fail+1)); fi
  local dt=$(( $(date +%s) - t0 ))
  echo "| $name | $r | ${dt}s | $(tail -1 "$W/step.log" | tr '|' '/' | cut -c1-140) |" | tee -a "$REPORT"
  cp "$W/step.log" "$W/log_$(echo "$name" | tr -c 'a-zA-Z0-9' '_').txt"
}
{
  echo "# End-to-end verification from scratch"; echo
  echo "Run on $(uname -sm), $(nproc) CPU, $(date -u +%Y-%m-%dT%H:%MZ). Fresh clone of commit \`$(git -C "$SRC" rev-parse --short HEAD)\`, fresh virtualenv."; echo
  echo "| step | result | wall | last line of output |"; echo "|---|---|---|---|"
} > "$REPORT"

step "git clone (committed files only)" git clone -q "$SRC" "$W/repo"
cd "$W/repo"
step "fresh virtualenv + pip install -r requirements.txt" bash -c "python3 -m venv $W/venv && $W/venv/bin/pip install -q -r requirements.txt && $W/venv/bin/python -c 'import numpy,httpx,fastapi,uvicorn,yaml;print(\"deps ok\")'"
export PATH="$W/venv/bin:$PATH"
step "unit + simulator tests (pytest)" python -m pytest -q tests
step "controller never reads simulator internals" bash -c "! grep -rnE 'import sim|from sim|runs/|scenarios/|\.yaml' controller/ && echo 'no access to sim/, runs/ or scenario files'"
step "public_01 end to end via run.sh" bash -c "scripts/run_scenario.sh scenarios/public_01_dev.yaml public_01 8931 >/dev/null && sed -n 10p reports/public_01.md"
step "public_02 end to end via run.sh" bash -c "scripts/run_scenario.sh scenarios/public_02_incidents.yaml public_02 8932 >/dev/null && sed -n 10p reports/public_02.md && grep -m1 mttr reports/public_02.md"
step "audit: why did ks_cancel change (public_02)" bash -c "python -m controller why --db state/public_02.db --workflow ks_cancel --at 'D3 16:00' | head -3 | tail -1"
step "audit: what a customer heard" bash -c "P=\$(python -c \"import sqlite3;print(sqlite3.connect('state/public_02.db').execute('select person_id from calls_heard limit 1').fetchone()[0])\"); python -m controller heard --db state/public_02.db --person \$P | sed -n 3p | cut -c1-120"
step "supervisor view serves HTML + JSON (token on)" bash -c "VIEW_TOKEN=t python -m controller view --db state/public_02.db --port 8939 & sleep 4; a=\$(curl -s -o /dev/null -w '%{http_code}' localhost:8939/tenant/kestrel_finance); b=\$(curl -s -o /dev/null -w '%{http_code}' -H 'Authorization: Bearer t' localhost:8939/tenant/kestrel_finance); c=\$(curl -s -H 'Authorization: Bearer t' localhost:8939/api/loop | python -c 'import json,sys;print(json.load(sys.stdin)[\"chunks_ingested\"])'); kill %1; echo \"no token -> \$a, token -> \$b, loop chunks \$c\"; [ \$a = 401 ] && [ \$b = 200 ]"
step "crash-recovery test (injected + random kills)" bash -c "python scripts/crash_test.py --kills 4 | grep -E 'Result'"
step "edge cases (9 scenarios)" bash -c "python scripts/edge_cases.py | tail -1"
if [ "${SKIP_DOCKER:-0}" != "1" ]; then
  BI="${BASE_IMAGE:-python:3.12-slim}"
  step "docker build controller (--no-cache, base $BI)" docker build --no-cache -q --build-arg BASE_IMAGE="$BI" -t formi-controller .
  step "docker build simulator (--no-cache, base $BI)" docker build --no-cache -q --build-arg BASE_IMAGE="$BI" -f Dockerfile.sim -t formi-sim .
  step "docker compose: sim + controller run public_01 to the end" bash -c "export SCENARIO=public_01_dev BASE_IMAGE=$BI; rm -rf state/docker_public_01_dev runs/docker_public_01_dev; docker compose up --build --abort-on-container-exit --exit-code-from controller sim controller >/dev/null 2>&1; rc=\$?; docker compose down >/dev/null 2>&1; [ \$rc = 0 ] && python -m sim grade --run runs/docker_public_01_dev/mine --baseline runs/base_public_01 | sed -n 10p"
  step "run.sh USE_DOCKER=1 against a host simulator (public_02)" bash -c "python -m sim serve --scenario scenarios/public_02_incidents.yaml --run-dir runs/dock02 --force --port 8933 >/dev/null 2>&1 & sleep 8; rm -rf state/dock02; CONTROLLER_DB=state/dock02/controller.db USE_DOCKER=1 BASE_IMAGE=$BI ./run.sh http://127.0.0.1:8933 >/dev/null 2>&1; rc=\$?; kill %1; [ \$rc = 0 ] && python -m sim grade --run runs/dock02 --baseline runs/base_public_02 | sed -n 10p"
  step "docker: kill controller container mid-run, restart, finish" bash -c "python -m sim serve --scenario scenarios/public_01_dev.yaml --run-dir runs/dockk --force --port 8934 >/dev/null 2>&1 & sleep 8; rm -rf state/dockk; mkdir -p state/dockk; docker run -d --name e2e_ctl --network host -v \$PWD/state/dockk:/app/state formi-controller run --url http://127.0.0.1:8934 --db /app/state/c.db >/dev/null; sleep 15; docker kill e2e_ctl >/dev/null; docker rm e2e_ctl >/dev/null; docker run --rm --network host -v \$PWD/state/dockk:/app/state formi-controller run --url http://127.0.0.1:8934 --db /app/state/c.db >/dev/null 2>&1; rc=\$?; kill %1; [ \$rc = 0 ] && python -c \"import sqlite3;d=sqlite3.connect('state/dockk/c.db');print('restarted ok; decisions:', d.execute('select count(*) from decisions where kind=\\\"recovery.restart\\\"').fetchone()[0], 'restart(s) recorded')\""
fi
{ echo; echo "**$pass passed, $fail failed.** Logs for each step are next to this report in \`$W\`."; } >> "$REPORT"
cp "$REPORT" "$SRC/reports/e2e_from_scratch.md"
cat "$REPORT"
[ "$fail" = 0 ]
