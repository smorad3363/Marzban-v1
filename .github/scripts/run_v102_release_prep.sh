#!/usr/bin/env bash
set -Eeuo pipefail

python .github/scripts/apply_v102_release_prep.py

pushd app/dashboard >/dev/null
npm ci
VITE_BASE_API=/api/ npm run build -- --outDir build --assetsDir statics
cp build/index.html build/404.html
popd >/dev/null

{ git diff --name-only; git ls-files --others --exclude-standard; } | sort -u > /tmp/v102-release-changed
while IFS= read -r path; do
  case "$path" in
    VERSION|app/__init__.py|scripts/marzban.sh|docker-compose.yml|README.md|README-fa.md|tests/release_installer_lab.sh|tests/release_upgrade_lab.sh|tests/test_installer_v1_contract.sh|tests/test_release_contract.py|docs/RELEASE_NOTES_v1.0.2.md|docs/CODEX/STATE.md|app/dashboard/build/*) ;;
    *) echo "Unexpected release-prep path: $path" >&2; exit 1 ;;
  esac
done < /tmp/v102-release-changed

test "$(tr -d '[:space:]' < VERSION)" = 1.0.2
grep -Fx '__version__ = "1.0.2"' app/__init__.py
grep -Fx 'CLI_RELEASE_VERSION="v1.0.2"' scripts/marzban.sh
grep -Fq 'ghcr.io/smorad3363/marzban-v1:v1.0.2' docker-compose.yml
grep -Fx 'V1_LINEAGE_TARGET_VERSION="v1.0.0"' scripts/marzban.sh
bash -n scripts/marzban.sh
bash -n tests/release_installer_lab.sh
bash -n tests/release_upgrade_lab.sh
bash tests/test_installer_v1_contract.sh
python -m pytest -q tests/test_release_contract.py tests/test_v102_node_deployment.py
python - <<'PY'
import yaml
from pathlib import Path
for path in (
    '.github/workflows/release-v1.yml',
    '.github/workflows/verify-v1-image.yml',
    '.github/workflows/validate-v1-installer.yml',
    '.github/workflows/v1.0.2-checkpoints.yml',
):
    yaml.safe_load(Path(path).read_text())
PY

git grep -n -E 'v1\.0\.1|1\.0\.1' -- VERSION app/__init__.py scripts/marzban.sh docker-compose.yml README.md README-fa.md tests .github/workflows > /tmp/v102-stale || true
grep -v -F '! is_allowed_v1_lineage_transition "5.2.0" "v1.0.1"' /tmp/v102-stale > /tmp/v102-unexpected-stale || true
if [ -s /tmp/v102-unexpected-stale ]; then
  cat /tmp/v102-unexpected-stale >&2
  exit 1
fi

test -s app/dashboard/build/index.html
test -s app/dashboard/build/404.html
grep -RFq '1.0.2' app/dashboard/build
git diff --check

git config user.name "Eliot"
git config user.email "42266703+smorad3363@users.noreply.github.com"
git add -A -- VERSION app/__init__.py scripts/marzban.sh docker-compose.yml README.md README-fa.md tests/release_installer_lab.sh tests/release_upgrade_lab.sh tests/test_installer_v1_contract.sh tests/test_release_contract.py docs/RELEASE_NOTES_v1.0.2.md docs/CODEX/STATE.md app/dashboard/build
git diff --cached --check
git diff --cached --quiet && { echo 'No release-prep changes to commit' >&2; exit 1; }
git commit -m "release: prepare Marzban v1.0.2"
git push origin HEAD:release/v1.0.2
