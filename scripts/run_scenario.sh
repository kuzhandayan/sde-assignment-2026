#!/usr/bin/env bash
# Run one scenario end to end locally: simulator + controller + grade, with live progress.
#   scripts/run_scenario.sh scenarios/public_01_dev.yaml public_01 [port]
# Full logs: logs/sim_<name>.log and logs/controller_<name>.log
set -uo pipefail
SCEN="$1"; NAME="$2"; PORT="${3:-8700}"
cd "$(dirname "$0")/.."
mkdir -p reports state logs
say() { echo "[$(date +%H:%M:%S)] $*"; }
fail() { say "FAILED: $*"; exit 1; }

if [ ! -d "runs/base_$NAME" ]; then
  say "baseline: running the no-op controller for comparison (~10 s)..."
  python -m sim baseline --scenario "$SCEN" --run-dir "runs/base_$NAME" > "logs/baseline_$NAME.log" 2>&1 \
    || { tail -20 "logs/baseline_$NAME.log"; fail "baseline (see logs/baseline_$NAME.log)"; }
fi
rm -f "state/$NAME.db" "state/$NAME.db-wal" "state/$NAME.db-shm" "state/$NAME.db.lock"

if curl -s "http://127.0.0.1:$PORT/health" >/dev/null 2>&1; then
  fail "port $PORT is already in use (an old simulator still running?). Stop it: pkill -f 'sim serve'"
fi
say "simulator: starting $SCEN on port $PORT (log: logs/sim_$NAME.log)"
python -m sim serve --scenario "$SCEN" --run-dir "runs/mine_$NAME" --force --port "$PORT" > "logs/sim_$NAME.log" 2>&1 &
SIM_PID=$!
trap 'kill $SIM_PID 2>/dev/null || true' EXIT
for i in $(seq 1 240); do
  curl -s "http://127.0.0.1:$PORT/health" >/dev/null 2>&1 && break
  if ! kill -0 $SIM_PID 2>/dev/null; then
    echo "---- last lines of logs/sim_$NAME.log ----"; tail -25 "logs/sim_$NAME.log"
    fail "simulator crashed while starting (see above)"
  fi
  [ $((i % 5)) = 0 ] && say "simulator: still generating the world... (${i}s)"
  sleep 1
done
curl -s "http://127.0.0.1:$PORT/health" >/dev/null 2>&1 || fail "simulator did not come up in 240 s"
say "simulator: ready"

say "controller: running (one line per simulated day; log: logs/controller_$NAME.log)"
CONTROLLER_WAIT_S=60 CONTROLLER_DB="state/$NAME.db" ./run.sh "http://127.0.0.1:$PORT" 2>&1 \
  | tee "logs/controller_$NAME.log" \
  | while IFS= read -r line; do
      case "$line" in
        *"INFO controller: "*) echo "[${line:11:8}] controller: ${line#*INFO controller: }" ;;
        *ERROR*|*Traceback*|*Error*|*rror:*) echo "$line" ;;
      esac
    done
RC=${PIPESTATUS[0]}
if [ $RC != 0 ]; then
  echo "---- last lines of logs/controller_$NAME.log ----"; tail -25 "logs/controller_$NAME.log"
  fail "controller exited with code $RC"
fi
say "grading against the baseline..."
python -m sim grade --run "runs/mine_$NAME" --baseline "runs/base_$NAME" --out "reports/$NAME.md" > /dev/null \
  || fail "grading"
python -m controller report --db "state/$NAME.db" --out "reports/supervisor_$NAME.md" > /dev/null 2>&1 || true
say "done -> reports/$NAME.md"
sed -n 5,10p "reports/$NAME.md"
