#!/usr/bin/env bash
# What `docker compose up` runs: the live supervisor view, then tests + each scenario end to end
# (simulator + controller + grade). Edit any .py file in controller/ and the run restarts with the new code.
# SCENARIOS overrides the list of scenarios.
set -uo pipefail
set -m                      # job control: each background run is its own process group, so it can be stopped whole
cd "$(dirname "$0")/.."
SCENARIOS="${SCENARIOS:-public_01_dev public_02_incidents}"
say() { echo "[$(date +%H:%M:%S)] $*"; }
changed() { find controller -name '*.py' -newer /tmp/.code_stamp 2>/dev/null | head -1; }

run_all() {
  say "== unit tests"
  python -m pytest -q -p no:cacheprovider tests || return 1
  port=8701
  for s in $SCENARIOS; do
    name="${s%%_*}_${s#*_}"; name="${name%_*}"            # public_02_incidents -> public_02
    echo; say "== scenario $s"
    USE_DOCKER=0 scripts/run_scenario.sh "scenarios/$s.yaml" "$name" "$port" || return 1
    port=$((port + 1))
  done
  echo; say "== all done. View: http://localhost:8800 · edit code in controller/ to re-run · Ctrl+C to stop"
}

port_free() { python -c "import socket,sys; s=socket.socket(); sys.exit(s.connect_ex(('127.0.0.1', $1)) == 0)"; }

stop_run() {                # stop tests, simulator and controller of the current run (one process group)
  kill -TERM -- -"$RUN" 2>/dev/null; sleep 1; kill -KILL -- -"$RUN" 2>/dev/null; wait "$RUN" 2>/dev/null
  for p in 8701 8702 8703 8704; do for i in $(seq 1 20); do port_free $p && break; sleep 0.5; done; done
}

python -m controller view --db state --host 0.0.0.0 --port 8800 &
say "== supervisor view: http://localhost:8800 (refreshes by itself; follows the run in progress)"

while true; do
  touch /tmp/.code_stamp
  run_all & RUN=$!
  while [ -z "$(changed)" ]; do sleep 2; done            # keep running until the code changes
  echo; say "== code changed ($(changed)): restarting the run with the new code"
  stop_run
done
