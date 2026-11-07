#!/usr/bin/env bash
# What `docker compose up` runs: tests, then each scenario end to end (simulator + controller + grade),
# then the supervisor view of the last one. SCENARIOS overrides the list.
set -uo pipefail
cd "$(dirname "$0")/.."
SCENARIOS="${SCENARIOS:-public_01_dev public_02_incidents}"
say() { echo "[$(date +%H:%M:%S)] $*"; }

say "== unit tests"
python -m pytest -q -p no:cacheprovider tests || exit 1

port=8701
for s in $SCENARIOS; do
  name="${s%%_*}_${s#*_}"; name="${name%_*}"            # public_02_incidents -> public_02
  echo; say "== scenario $s"
  USE_DOCKER=0 scripts/run_scenario.sh "scenarios/$s.yaml" "$name" "$port" || exit 1
  last="$name"; port=$((port + 1))
done

echo; say "== all done. Supervisor view of $last: http://localhost:8800  (Ctrl+C to stop)"
exec python -m controller view --db "state/$last.db" --host 0.0.0.0 --port 8800
