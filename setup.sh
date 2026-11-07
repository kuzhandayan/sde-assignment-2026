#!/usr/bin/env bash
# One-time setup + smoke test (macOS or Linux):  ./setup.sh
# Creates .venv, installs requirements, runs the unit tests and one full scenario end to end.
set -euo pipefail
cd "$(dirname "$0")"
PY="$(command -v python3.12 || command -v python3.11 || command -v python3)"
echo "Using $($PY --version) at $PY"
[ -d .venv ] || "$PY" -m venv .venv
.venv/bin/python -m pip install -q --upgrade pip
.venv/bin/python -m pip install -q -r requirements.txt
export PATH="$PWD/.venv/bin:$PATH"
echo "== unit tests"
python -m pytest -q tests
echo "== public_01 end to end (about 1 minute)"
scripts/run_scenario.sh scenarios/public_01_dev.yaml public_01 8701 >/dev/null
sed -n 5,10p reports/public_01.md
cat <<'MSG'

Ready. Activate the environment with:   source .venv/bin/activate
Then try:
  scripts/run_scenario.sh scenarios/public_02_incidents.yaml public_02 8702
  python -m controller why  --db state/public_02.db --workflow ks_cancel --at "D3 16:30"
  python -m controller view --db state/public_02.db        # open http://127.0.0.1:8800
  python scripts/crash_test.py --kills 4
  python scripts/edge_cases.py
  SCENARIO=public_01_dev docker compose up --build sim controller   # Docker check (needs Docker Desktop)
MSG
