#!/usr/bin/env bash
set -Eeuo pipefail

REPO="${MARZBAN_TEST_REPO:-https://github.com/smorad3363/Marzban-v1.git}"
BRANCH="${MARZBAN_TEST_BRANCH:-release/v1.0.3}"
EXPECTED_VERSION="${MARZBAN_TEST_VERSION:-1.0.3}"
IMAGE="${MARZBAN_TEST_IMAGE:-marzban-v1:test-v1.0.3}"
PROJECT="${MARZBAN_COMPOSE_PROJECT:-marzban}"

cd /

for cmd in docker git yq; do
  command -v "$cmd" >/dev/null 2>&1 || { echo "ERROR: $cmd is required" >&2; exit 1; }
done

docker compose version >/dev/null 2>&1 || { echo "ERROR: docker compose is required" >&2; exit 1; }

COMPOSE="${MARZBAN_COMPOSE_FILE:-}"
if [ -z "$COMPOSE" ]; then
  for candidate in \
    /opt/marzban/docker-compose.yml \
    /opt/marzban/docker-compose.yaml \
    /var/lib/marzban/docker-compose.yml \
    /var/lib/marzban/docker-compose.yaml
  do
    if [ -f "$candidate" ]; then
      COMPOSE="$candidate"
      break
    fi
  done
fi

if [ -z "$COMPOSE" ]; then
  COMPOSE="$(find /opt /var/lib -maxdepth 4 -type f \( -name docker-compose.yml -o -name docker-compose.yaml \) 2>/dev/null | grep -m1 -E '/marzban/' || true)"
fi

[ -n "$COMPOSE" ] && [ -f "$COMPOSE" ] || { echo "ERROR: Marzban compose file not found" >&2; exit 1; }

OLD_IMAGE="$(yq -r '.services.marzban.image // ""' "$COMPOSE")"
[ -n "$OLD_IMAGE" ] || { echo "ERROR: current Marzban image not found in $COMPOSE" >&2; exit 1; }

STAMP="$(date +%Y%m%d-%H%M%S)"
BACKUP="${COMPOSE}.before-${EXPECTED_VERSION}-test.${STAMP}"
ROLLBACK_TAG="marzban-v1:pretest-${STAMP}"
cp -a "$COMPOSE" "$BACKUP"
if docker image inspect "$OLD_IMAGE" >/dev/null 2>&1; then
  docker tag "$OLD_IMAGE" "$ROLLBACK_TAG"
else
  ROLLBACK_TAG=""
fi
WORKDIR="$(mktemp -d /tmp/marzban-v103.XXXXXX)"
SWITCHED=0

cleanup() {
  cd /
  rm -rf "$WORKDIR" 2>/dev/null || true
}

rollback() {
  rc=$?
  trap - ERR
  echo
  echo "TEST FAILED (exit $rc)"
  if [ "$SWITCHED" -eq 1 ]; then
    echo "Rolling back to: $OLD_IMAGE"
    cp -a "$BACKUP" "$COMPOSE"
    if [ -n "$ROLLBACK_TAG" ] && docker image inspect "$ROLLBACK_TAG" >/dev/null 2>&1; then
      docker tag "$ROLLBACK_TAG" "$OLD_IMAGE" || true
    fi
    docker compose -f "$COMPOSE" -p "$PROJECT" up -d --no-deps --force-recreate marzban || true
  else
    echo "Runtime was not switched; nothing to roll back."
  fi
  cleanup
  exit "$rc"
}
trap rollback ERR

printf 'Compose: %s\nCurrent image: %s\nBranch: %s\n' "$COMPOSE" "$OLD_IMAGE" "$BRANCH"

echo "==> Fetching source"
git clone --depth 1 --branch "$BRANCH" "$REPO" "$WORKDIR"
cd "$WORKDIR"

SOURCE_VERSION="$(tr -d '\r\n ' < VERSION)"
[ "$SOURCE_VERSION" = "$EXPECTED_VERSION" ] || {
  echo "ERROR: source VERSION is $SOURCE_VERSION, expected $EXPECTED_VERSION" >&2
  exit 1
}

COMMIT="$(git rev-parse --short HEAD)"
echo "Source: $EXPECTED_VERSION @ $COMMIT"

echo "==> Building dashboard"
docker run --rm \
  -v "$WORKDIR:/repo" \
  -w /repo/app/dashboard \
  node:20-bookworm-slim \
  sh -lc 'npm ci && npm run build'

[ -s "$WORKDIR/app/dashboard/build/index.html" ] || {
  echo "ERROR: dashboard build did not produce build/index.html" >&2
  exit 1
}

echo "==> Building test image"
docker build -t "$IMAGE" "$WORKDIR"

echo "==> Switching Marzban to local test image"
yq -i ".services.marzban.image = \"${IMAGE}\"" "$COMPOSE"
SWITCHED=1
cd /
docker compose -f "$COMPOSE" -p "$PROJECT" up -d --no-deps --force-recreate marzban

CID=""
for _ in $(seq 1 90); do
  CID="$(docker compose -f "$COMPOSE" -p "$PROJECT" ps -q marzban 2>/dev/null || true)"
  if [ -n "$CID" ]; then
    RUNNING="$(docker inspect -f '{{.State.Running}}' "$CID" 2>/dev/null || true)"
    HEALTH="$(docker inspect -f '{{if .State.Health}}{{.State.Health.Status}}{{else}}none{{end}}' "$CID" 2>/dev/null || true)"
    if [ "$RUNNING" = "true" ] && { [ "$HEALTH" = "healthy" ] || [ "$HEALTH" = "none" ]; }; then
      break
    fi
  fi
  sleep 2
done

[ -n "$CID" ] || { echo "ERROR: Marzban container was not created" >&2; exit 1; }
[ "$(docker inspect -f '{{.State.Running}}' "$CID")" = "true" ] || { docker logs --tail 120 "$CID" || true; exit 1; }

RUNTIME="$(docker exec "$CID" python -c 'from app import __version__; print(__version__)' 2>/dev/null | tr -d '\r\n ' || true)"
[ "$RUNTIME" = "$EXPECTED_VERSION" ] || {
  echo "ERROR: runtime version is '${RUNTIME:-unknown}', expected $EXPECTED_VERSION" >&2
  docker logs --tail 120 "$CID" || true
  exit 1
}

if docker exec "$CID" test -f /code/scripts/healthcheck.py; then
  docker exec "$CID" python /code/scripts/healthcheck.py --mode internal --timeout 5
fi

trap - ERR
cleanup

echo
echo "============================================"
echo "v${EXPECTED_VERSION} TEST DEPLOYED SUCCESSFULLY"
echo "Commit:  $COMMIT"
echo "Runtime: $RUNTIME"
echo "Image:   $IMAGE"
echo "Backup:  $BACKUP"
[ -n "$ROLLBACK_TAG" ] && echo "Rollback image: $ROLLBACK_TAG"
echo "============================================"
docker compose -f "$COMPOSE" -p "$PROJECT" ps
