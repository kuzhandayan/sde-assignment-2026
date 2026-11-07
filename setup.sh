#!/usr/bin/env bash
# One-time setup + smoke test (macOS or Linux):  ./setup.sh
# Creates .venv, installs requirements, runs the unit tests and one full scenario end to end.
# Needs Python 3.10+ (the provided simulator uses 3.10 syntax). macOS's built-in python3 is 3.9: install a newer
# one with `brew install python@3.12` (or from python.org) and re-run.
set -euo pipefail
cd "$(dirname "$0")"

PY=""
for c in python3.13 python3.12 python3.11 python3.10 \
         /opt/homebrew/bin/python3 "$HOME/.homebrew/bin/python3" /usr/local/bin/python3 python3; do
  p="$(command -v "$c" 2>/dev/null || true)"
  [ -n "$p" ] || continue
  if "$p" -c 'import sys; sys.exit(0 if sys.version_info >= (3, 10) else 1)' 2>/dev/null; then PY="$p"; break; fi
done
if [ -z "$PY" ]; then
  echo "ERROR: Python 3.10 or newer is required (found: $(python3 --version 2>&1))."
  echo "On macOS:  brew install python@3.12     (or download from https://www.python.org/downloads/)"
  echo "Then run ./setup.sh again."
  exit 1
fi
echo "[1/4] Using $($PY --version) at $PY"

if [ -d .venv ] && ! .venv/bin/python -c 'import sys; sys.exit(0 if sys.version_info >= (3, 10) else 1)' 2>/dev/null; then
  echo "      removing old .venv built with an older Python"
  rm -rf .venv
fi
[ -d .venv ] || "$PY" -m venv .venv
echo "[2/4] Installing packages (1-2 minutes the first time)..."
.venv/bin/python -m pip install --disable-pip-version-check --progress-bar on -r requirements.txt
export PATH="$PWD/.venv/bin:$PATH"

echo "[3/4] Unit tests"
python -m pytest -q tests

echo "[4/4] public_01 end to end as a smoke test (about 1 minute; writes reports/smoke_public_01.md, the official reports are not touched)"
scripts/run_scenario.sh scenarios/public_01_dev.yaml smoke_public_01 8701 || exit 1
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
