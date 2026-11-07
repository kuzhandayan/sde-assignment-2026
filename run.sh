#!/usr/bin/env bash
# Contract: ./run.sh <SIM_URL> starts the controller and runs until the scenario finishes. No manual steps.
#
#   ./run.sh http://127.0.0.1:8700                  # plain Python (default; needs requirements.txt installed)
#   USE_DOCKER=1 ./run.sh http://127.0.0.1:8700     # same controller inside Docker (host networking)
#
# State lives in $CONTROLLER_DB (default state/controller.db). Re-running with the same DB resumes after a
# crash; for a NEW simulator run use a new/empty DB (the controller refuses to mix two worlds).
set -euo pipefail
SIM_URL="${1:?usage: ./run.sh <SIM_URL>}"
cd "$(dirname "$0")"
DB="${CONTROLLER_DB:-state/controller.db}"
mkdir -p "$(dirname "$DB")"
if [ "${USE_DOCKER:-0}" = "1" ]; then
  docker build -q ${BASE_IMAGE:+--build-arg BASE_IMAGE=$BASE_IMAGE} -t formi-controller . >/dev/null
  NET="--network host"
  if [ "$(uname)" = "Darwin" ]; then
    # Docker Desktop on macOS: reach the host's simulator through host.docker.internal instead
    NET=""
    SIM_URL="$(echo "$SIM_URL" | sed -e 's#127.0.0.1#host.docker.internal#' -e 's#localhost#host.docker.internal#')"
  fi
  exec docker run --rm $NET -v "$PWD/$(dirname "$DB")":/app/state formi-controller \
       run --url "$SIM_URL" --db "/app/state/$(basename "$DB")"
fi
exec python -m controller run --url "$SIM_URL" --db "$DB"
