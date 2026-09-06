#!/usr/bin/env bash
# Run only on an isolated disposable Linux release runner.
set -euo pipefail

test "${RELEASE_DISPOSABLE_LAB:-}" = "1"
[[ "${RELEASE_SOURCE_COMMIT:-}" =~ ^[0-9a-f]{40}$ ]]
[[ "${RELEASE_IMAGE_DIGEST:-}" =~ ^sha256:[0-9a-f]{64}$ ]]
[[ "${RELEASE_TAG:-}" =~ ^v[0-9]+\.[0-9]+\.[0-9]+$ ]]
test "$(id -u)" = "0"
test ! -e /opt/marzban
test ! -e /var/lib/marzban

runtime_version="${RELEASE_TAG#v}"
installer_url="https://raw.githubusercontent.com/smorad3363/Marzban-v1/${RELEASE_TAG}/scripts/marzban.sh"
installer="$(curl -fsSL "$installer_url")"
bash -n <<< "$installer"
grep -Fq "CLI_RELEASE_VERSION=\"${RELEASE_TAG}\"" <<< "$installer"
grep -Fq 'MARZBAN_GITHUB_REPO="${MARZBAN_GITHUB_REPO:-smorad3363/Marzban-v1}"' <<< "$installer"

require_fixed_line() {
  local expected="$1"
  local actual="$2"
  if ! grep -Fxq -- "$expected" <<< "$actual"; then
    printf 'Expected exact line: %s\nActual output:\n%s\n' "$expected" "$actual" >&2
    return 1
  fi
}

printf '\n' | bash -c "$installer" @ install --version "$RELEASE_TAG" --database mysql
printf '%s\n' 'Release-Disposable-Owner-927' | marzban create-owner release_owner
version_output="$(marzban version)"
require_fixed_line "CLI version: ${RELEASE_TAG}" "$version_output"
require_fixed_line "Runtime app version: ${runtime_version}" "$version_output"
require_fixed_line "Immutable image digest: ghcr.io/smorad3363/marzban-v1@${RELEASE_IMAGE_DIGEST}" "$version_output"
require_fixed_line "Source revision: ${RELEASE_SOURCE_COMMIT}" "$version_output"
owner_row="$(docker exec marzban-mysql-1 sh -c \
  'MYSQL_PWD="$MYSQL_ROOT_PASSWORD" mysql -uroot "$MYSQL_DATABASE" -N -e "SELECT username FROM admins WHERE username='\''release_owner'\'';"')"
require_fixed_line release_owner "$owner_row"

before="$(sha256sum /opt/marzban/.env)"
if bash -c "$installer" @ install --version "$RELEASE_TAG" --database mysql; then
  echo 'Reinstall unexpectedly succeeded' >&2
  exit 1
fi
test "$before" = "$(sha256sum /opt/marzban/.env)"
if marzban rollback v0.9.0; then
  echo 'Downgrade unexpectedly succeeded' >&2
  exit 1
fi

printf '%s\n' "FRESH_INSTALL_CREATE_OWNER_VERSION_PASS ${RELEASE_TAG}"
