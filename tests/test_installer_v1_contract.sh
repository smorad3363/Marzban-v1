#!/usr/bin/env bash
set -eo pipefail

source scripts/marzban.sh
set -u

# Preserve the one-time historical migration contract from v5.2.0 to v1.0.0.
is_allowed_v1_lineage_transition \
  "5.2.0" \
  "v1.0.0" \
  "ghcr.io/smorad3363/marzban-vnext:v5.2.0" \
  "ghcr.io/smorad3363/marzban-vnext:v5.2.0"
! is_allowed_v1_lineage_transition "5.2.1" "v1.0.0" "$V1_LINEAGE_SOURCE_IMAGE" "$V1_LINEAGE_SOURCE_IMAGE"
! is_allowed_v1_lineage_transition "5.2.0" "v1.0.1" "$V1_LINEAGE_SOURCE_IMAGE" "$V1_LINEAGE_SOURCE_IMAGE"
! is_allowed_v1_lineage_transition "5.2.0" "v1.0.0" "ghcr.io/example/other:v5.2.0" "$V1_LINEAGE_SOURCE_IMAGE"
! is_allowed_v1_lineage_transition "5.2.0" "v1.0.0" "$V1_LINEAGE_SOURCE_IMAGE" "ghcr.io/example/other:v5.2.0"

test_root="$(mktemp -d)"
trap 'rm -rf -- "$test_root"' EXIT
printf '#!/usr/bin/env bash\nexit 0\n' > "$test_root/yq"
chmod 700 "$test_root/yq"
PATH="$test_root:$PATH"
COMPOSE_FILE="$test_root/docker-compose.yml"
touch "$COMPOSE_FILE"

check_running_as_root() { :; }
is_marzban_installed() { return 0; }
detect_compose() { COMPOSE=mock_compose; }
is_marzban_up() { return 0; }
configured_service_image() {
  case "$1" in
    marzban) printf '%s\n' "ghcr.io/smorad3363/marzban-v1:v1.0.7" ;;
    mysql) printf '%s\n' "mysql:26.7.0" ;;
  esac
}
running_service_container() { printf '%s-id\n' "$1"; }
runtime_app_version() { printf '%s\n' "1.0.7"; }
marzban_image_revision() { printf '%040d\n' 1; }
mysql_upgrade_server_version() { printf '%s\n' "26.7.0"; }
verify_version_integrity() {
  test "$1" = "v1.0.7"
  printf '%s\n' "INTEGRITY_OK"
}
docker() {
  if [[ "$*" == *".Config.Image"* ]]; then
    printf '%s\n' "ghcr.io/smorad3363/marzban-v1:v1.0.7"
  elif [[ "$*" == *".RepoDigests"* ]]; then
    printf '%s\n' "ghcr.io/smorad3363/marzban-v1@sha256:$(printf '%064d' 2)"
  fi
}

version_output="$(version_command)"
grep -Fxq "CLI version: v1.0.7" <<< "$version_output"
grep -Fxq "Runtime app version: 1.0.7" <<< "$version_output"
grep -Fxq "Configured Docker image: ghcr.io/smorad3363/marzban-v1:v1.0.7" <<< "$version_output"
grep -Fxq "Configured MySQL image: mysql:26.7.0" <<< "$version_output"
grep -Fxq "Runtime MySQL version: 26.7.0" <<< "$version_output"
grep -Fxq "INTEGRITY_OK" <<< "$version_output"

APP_NAME=marzban
CALL_FILE="$test_root/owner-call"
PASSWORD_FILE="$test_root/owner-password"
export CALL_FILE PASSWORD_FILE
mock_compose() {
  printf '%s\n' "$*" > "$CALL_FILE"
  printf '%s' "${MARZBAN_ADMIN_PASSWORD:-}" > "$PASSWORD_FILE"
}

printf '%s\n' "owner-secret" | create_owner_command release_owner >/dev/null
grep -Fq -- '-e MARZBAN_ADMIN_PASSWORD marzban marzban-cli admin bootstrap-owner --username release_owner' "$CALL_FILE"
! grep -Fq 'owner-secret' "$CALL_FILE"
grep -Fxq 'owner-secret' "$PASSWORD_FILE"
test -z "${MARZBAN_ADMIN_PASSWORD:-}"
grep -Fq 'Usage: marzban create-owner [USERNAME]' <<< "$(create_owner_command --help)"
if (create_owner_command release_owner unexpected >/dev/null 2>&1); then
  echo "create-owner accepted unexpected arguments" >&2
  exit 1
fi

printf '%s\n' "INSTALLER_V1_CONTRACT_OK"
