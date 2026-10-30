#!/usr/bin/env bash
set -Eeuo pipefail
umask 077

# Disposable QA only. Never run on an existing Marzban host.
REPO="https://github.com/smorad3363/Marzban-v1.git"
SOURCE_SHA="f71bf44d72a5e759384691a04769739c19b5921a"
SRC_DIR="/opt/marzban-qa-src"
APP_DIR="/opt/marzban-qa"
DATA_DIR="/var/lib/marzban"
IMAGE="marzban-qa:${SOURCE_SHA:0:12}"
PROJECT="marzbanqa"

fail() { printf 'ERROR: %s\n' "$*" >&2; exit 1; }

[ "$(id -u)" -eq 0 ] || fail "Run as root."
[ -r /etc/os-release ] || fail "Could not identify operating system."
. /etc/os-release
[ "${ID:-}" = "ubuntu" ] && [ "${VERSION_ID:-}" = "24.04" ] ||
  fail "Use a fresh Ubuntu 24.04 LTS server for QA."

for directory in "$SRC_DIR" "$APP_DIR" "$DATA_DIR" /opt/marzban; do
  [ ! -e "$directory" ] || fail "Existing data at $directory. Use a new empty test server."
done

export DEBIAN_FRONTEND=noninteractive
apt-get update
apt-get install -y --no-install-recommends ca-certificates curl git openssl docker.io docker-compose-v2
systemctl enable --now docker
docker compose version >/dev/null || fail "Docker Compose V2 is unavailable."

git clone --quiet "$REPO" "$SRC_DIR"
git -C "$SRC_DIR" checkout --quiet --detach "$SOURCE_SHA"
[ "$(git -C "$SRC_DIR" rev-parse HEAD)" = "$SOURCE_SHA" ] ||
  fail "Source commit verification failed."

mkdir -p "$APP_DIR" "$DATA_DIR"
cp "$SRC_DIR/docker-compose.yml" "$APP_DIR/docker-compose.yml"
sed -i "s|image: ghcr.io/smorad3363/marzban-v1:v1.1.10|image: $IMAGE|" "$APP_DIR/docker-compose.yml"
sed -i "s|/opt/marzban/.env:/opt/marzban/.env:ro|$APP_DIR/.env:/opt/marzban/.env:ro|" "$APP_DIR/docker-compose.yml"
grep -q "image: $IMAGE" "$APP_DIR/docker-compose.yml" || fail "QA image replacement failed."
grep -q "$APP_DIR/.env:/opt/marzban/.env:ro" "$APP_DIR/docker-compose.yml" ||
  fail "QA configuration mount replacement failed."

db_root_pass="$(openssl rand -hex 24)"
db_user_pass="$(openssl rand -hex 24)"
cat > "$APP_DIR/.env" <<EOF
UVICORN_HOST=127.0.0.1
UVICORN_PORT=8000
MYSQL_ROOT_PASSWORD=$db_root_pass
MYSQL_DATABASE=marzban
MYSQL_USER=marzban
MYSQL_PASSWORD=$db_user_pass
SQLALCHEMY_DATABASE_URL=mysql+pymysql://marzban:$db_user_pass@127.0.0.1:3306/marzban
MYSQL_INNODB_BUFFER_POOL_SIZE=256M
EOF
chmod 600 "$APP_DIR/.env"
unset db_root_pass db_user_pass

docker build --pull --tag "$IMAGE" "$SRC_DIR"
cd "$APP_DIR"
docker compose --project-name "$PROJECT" --env-file .env up -d

printf '\nWaiting for the QA container health check...\n'
container_id="$(docker compose --project-name "$PROJECT" ps -q marzban)"
[ -n "$container_id" ] || fail "QA container was not created."
healthy=0
for _ in $(seq 1 90); do
  state="$(docker inspect --format '{{.State.Health.Status}}' "$container_id" 2>/dev/null || true)"
  if [ "$state" = healthy ]; then healthy=1; break; fi
  if [ "$state" = unhealthy ]; then break; fi
  sleep 2
done
if [ "$healthy" != 1 ]; then
  docker compose --project-name "$PROJECT" ps >&2 || true
  docker compose --project-name "$PROJECT" logs --tail=80 marzban >&2 || true
  fail "QA health check did not pass."
fi

printf '\nQA installation is healthy (source %s).\n' "$SOURCE_SHA"
printf 'Create the first administrator with:\n'
printf '  cd %s && docker compose -p %s exec marzban python3 /code/marzban-cli.py admin create --sudo\n' "$APP_DIR" "$PROJECT"
printf 'Connect privately from your computer using:\n'
printf '  ssh -L 8000:127.0.0.1:8000 root@YOUR_SERVER_IP\n'
printf 'Then open http://127.0.0.1:8000/dashboard/\n'
printf 'This is a test installation, not a published stable release.\n'