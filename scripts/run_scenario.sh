#!/usr/bin/env bash
# Run one scenario end to end locally: simulator + controller + grade.
#   scripts/run_scenario.sh scenarios/public_01_dev.yaml public_01 [port]
set -euo pipefail
SCEN="$1"; NAME="$2"; PORT="${3:-8700}"
cd "$(dirname "$0")/.."
mkdir -p reports state logs
[ -d "runs/base_$NAME" ] || python -m sim baseline --scenario "$SCEN" --run-dir "runs/base_$NAME"
rm -f "state/$NAME.db" "state/$NAME.db-wal" "state/$NAME.db-shm"
python -m sim serve --scenario "$SCEN" --run-dir "runs/mine_$NAME" --force --port "$PORT" > "logs/sim_$NAME.log" 2>&1 &
SIM_PID=$!
trap 'kill $SIM_PID 2>/dev/null || true' EXIT
CONTROLLER_DB="state/$NAME.db" ./run.sh "http://127.0.0.1:$PORT" 2>&1 | tee "logs/controller_$NAME.log" | grep -E "INFO controller:|ERROR|Traceback" || true
python -m sim grade --run "runs/mine_$NAME" --baseline "runs/base_$NAME" --out "reports/$NAME.md" > /dev/null
python -m controller report --db "state/$NAME.db" --out "reports/supervisor_$NAME.md" > /dev/null || true
echo "graded -> reports/$NAME.md"
