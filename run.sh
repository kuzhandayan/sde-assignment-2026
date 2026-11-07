#!/usr/bin/env bash
# ./run.sh <SIM_URL>   run the controller until the scenario finishes.
# Uses Docker when it is available (no local Python needed); otherwise Python 3.10+ with requirements.txt.
# USE_DOCKER=0 forces Python, USE_DOCKER=1 forces Docker.
set -euo pipefail
SIM_URL="${1:?usage: ./run.sh <SIM_URL>}"
cd "$(dirname "$0")"
DB="${CONTROLLER_DB:-state/controller.db}"
mkdir -p "$(dirname "$DB")"

docker_ok() { command -v docker >/dev/null 2>&1 && docker info >/dev/null 2>&1; }

if [ "${USE_DOCKER:-auto}" = "1" ] || { [ "${USE_DOCKER:-auto}" = "auto" ] && docker_ok; }; then
  if docker build -q ${BASE_IMAGE:+--build-arg BASE_IMAGE=$BASE_IMAGE} -t formi-controller . >/dev/null; then
    NET="--network host"
    if [ "$(uname)" = "Darwin" ]; then   # Docker Desktop: reach the host via host.docker.internal
      NET=""
      SIM_URL="$(echo "$SIM_URL" | sed -e 's#127.0.0.1#host.docker.internal#' -e 's#localhost#host.docker.internal#')"
    fi
    exec docker run --rm $NET -v "$PWD/$(dirname "$DB")":/app/state formi-controller \
         run --url "$SIM_URL" --db "/app/state/$(basename "$DB")"
  fi
  [ "${USE_DOCKER:-auto}" = "1" ] && exit 1
  echo "run.sh: docker build failed; running with local Python instead" >&2
fi
exec python3 -m controller run --url "$SIM_URL" --db "$DB"
