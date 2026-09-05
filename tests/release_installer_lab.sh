#!/usr/bin/env bash
# Run only on an isolated disposable Linux release runner.
set -euo pipefail

test "${RELEASE_DISPOSABLE_LAB:-}" = "1"
test "${RELEASE_SOURCE_COMMIT:-}" = "6bc7688a294bc603eb30f320428e3002288bb8b2"
test "${RELEASE_IMAGE_DIGEST:-}" = "sha256:99c1a1e20a042c3385e7c31ad9084ea233314e8f9047585a6c834a720a123906"
test "$(id -u)" = "0"
test ! -e /opt/marzban
test ! -e /var/lib/marzban

installer_url="https://raw.githubusercontent.com/smorad3363/Marzban-v1/v1.0.0/scripts/marzban.sh"
installer="$(curl -fsSL "$installer_url")"
bash -n <<< "$installer"
grep -Fq 'CLI_RELEASE_VERSION="v1.0.0"' <<< "$installer"
grep -Fq 'MARZBAN_GITHUB_REPO="${MARZBAN_GITHUB_REPO:-smorad3363/Marzban-v1}"' <<< "$installer"

printf '\n' | bash -c "$installer" @ install --version v1.0.0 --database mysql
printf '%s\n' 'Release-Disposable-Owner-927' | marzban create-owner release_owner
version_output="$(marzban version)"
grep -Fxq 'CLI version: v1.0.0' <<< "$version_output"
grep -Fxq 'Runtime app version: 1.0.0' <<< "$version_output"
grep -Fq "Immutable image digest: ghcr.io/smorad3363/marzban-v1@${RELEASE_IMAGE_DIGEST}" <<< "$version_output"
grep -Fxq "Source revision: ${RELEASE_SOURCE_COMMIT}" <<< "$version_output"
docker exec marzban-marzban-1 python /code/marzban-cli.py admin list --username release_owner | grep -Fq release_owner

before="$(sha256sum /opt/marzban/.env)"
if bash -c "$installer" @ install --version v1.0.0 --database mysql; then
  echo 'Reinstall unexpectedly succeeded' >&2
  exit 1
fi
test "$before" = "$(sha256sum /opt/marzban/.env)"
if marzban rollback v0.9.0; then
  echo 'Downgrade unexpectedly succeeded' >&2
  exit 1
fi

printf '%s\n' 'FRESH_INSTALL_CREATE_OWNER_VERSION_PASS'
