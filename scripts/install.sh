#!/usr/bin/env bash
set -Eeuo pipefail
# Stable entry point. The official installer resolves the latest stable release
# and uses that exact version for the image, Compose files, and installed CLI.
installer="$(mktemp)"
trap 'rm -f "$installer"' EXIT
curl --fail --silent --show-error --location --retry 3 \
  https://raw.githubusercontent.com/smorad3363/Marzban-v1/main/scripts/marzban.sh \
  --output "$installer"
bash "$installer" install --version latest --database mysql "$@"
