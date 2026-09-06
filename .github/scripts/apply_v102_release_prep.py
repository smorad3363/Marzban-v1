from pathlib import Path


def replace_once(path: str, old: str, new: str) -> None:
    p = Path(path)
    text = p.read_text(encoding="utf-8")
    count = text.count(old)
    if count != 1:
        raise SystemExit(f"{path}: expected one context match, found {count}")
    p.write_text(text.replace(old, new, 1), encoding="utf-8")


Path("VERSION").write_text("1.0.2\n", encoding="utf-8")
replace_once("app/__init__.py", '__version__ = "1.0.1"', '__version__ = "1.0.2"')
replace_once("scripts/marzban.sh", 'CLI_RELEASE_VERSION="v1.0.1"', 'CLI_RELEASE_VERSION="v1.0.2"')
replace_once(
    "docker-compose.yml",
    "image: ghcr.io/smorad3363/marzban-v1:v1.0.1",
    "image: ghcr.io/smorad3363/marzban-v1:v1.0.2",
)

# Current installer contract moves to 1.0.2; preserve the historical negative
# lineage assertion that proves 5.2.0 can transition only to v1.0.0.
installer_test = Path("tests/test_installer_v1_contract.sh")
t = installer_test.read_text(encoding="utf-8")
negative = '! is_allowed_v1_lineage_transition "5.2.0" "v1.0.1" "$V1_LINEAGE_SOURCE_IMAGE" "$V1_LINEAGE_SOURCE_IMAGE"'
if negative not in t:
    raise SystemExit("historical v1.0.1 lineage negative assertion missing")
t = t.replace("v1.0.1", "v1.0.2").replace("1.0.1", "1.0.2")
t = t.replace(
    '! is_allowed_v1_lineage_transition "5.2.0" "v1.0.2" "$V1_LINEAGE_SOURCE_IMAGE" "$V1_LINEAGE_SOURCE_IMAGE"',
    negative,
    1,
)
installer_test.write_text(t, encoding="utf-8")

readme = Path("README.md")
r = readme.read_text(encoding="utf-8")
r = r.replace(
    'sudo bash -c "$(curl -fsSL https://raw.githubusercontent.com/smorad3363/Marzban-v1/v1.0.1/scripts/marzban.sh)" @ install --version v1.0.1 --database mysql',
    'sudo bash -c "$(curl -fsSL https://raw.githubusercontent.com/smorad3363/Marzban-v1/v1.0.2/scripts/marzban.sh)" @ install --version v1.0.2 --database mysql',
    1,
)
old_node = '''# Marzban Node

The Marzban project introduces the [Marzban-node](https://github.com/gozargah/marzban-node), which revolutionizes infrastructure distribution. With Marzban-node, you can distribute your infrastructure across multiple locations, unlocking benefits such as redundancy, high availability, scalability, flexibility. Marzban-node empowers users to connect to different servers, offering them the flexibility to choose and connect to multiple servers instead of being limited to only one server.
For more detailed information and installation instructions, please refer to the [Marzban-node official documentation](https://github.com/gozargah/marzban-node)
'''
new_node = '''# Marzban Node

Marzban V1.0.2 includes **Built-in Node Runtime V2**. A Node uses the same versioned Marzban image as the panel, has no MySQL service, and keeps its state separately under `/opt/marzban-node` and `/var/lib/marzban-node`.

On the Node server, copy only the panel client **certificate** (public PEM). Never copy the panel private key. Then install the exact release:

```bash
sudo bash -c "$(curl -fsSL https://raw.githubusercontent.com/smorad3363/Marzban-v1/v1.0.2/scripts/marzban.sh)" @ node install --version v1.0.2 --client-cert-file /path/to/panel-client.crt
```

Useful commands:

```bash
marzban node status
marzban node logs
marzban node update --version v1.0.2
```

Node Runtime V2 uses strict certificate verification, durable event delivery, and capability-aware client-IP reporting. On a server that also hosts the panel, Node CLI updates are isolated in `/usr/local/bin/marzban-node` and do not overwrite the panel CLI or panel release metadata.
'''
if old_node not in r:
    raise SystemExit("README.md: stale external Node section not found")
r = r.replace(old_node, new_node, 1)
readme.write_text(r, encoding="utf-8")

readme_fa = Path("README-fa.md")
rf = readme_fa.read_text(encoding="utf-8")
rf = rf.replace(
    "این نسخه فقط از دیتابیس MySQL 8 پشتیبانی می‌کند. برای نصب از دستور زیر استفاده کنید:",
    "این نسخه فقط از دیتابیس MySQL پشتیبانی می‌کند. برای نصب نسخه دقیق V1.0.2 از دستور زیر استفاده کنید:",
    1,
)
rf = rf.replace(
    'sudo bash -c "$(curl -fsSL https://raw.githubusercontent.com/smorad3363/Marzban-v1/v1.0.1/scripts/marzban.sh)" @ install --version v1.0.1 --database mysql',
    'sudo bash -c "$(curl -fsSL https://raw.githubusercontent.com/smorad3363/Marzban-v1/v1.0.2/scripts/marzban.sh)" @ install --version v1.0.2 --database mysql',
    1,
)
rf = rf.replace(
    "- فایل های مهم (اطلاعات) مرزبان در مسیر `/usr/lib/marzban` قرار می‌گیرند",
    "- فایل های مهم (اطلاعات) مرزبان در مسیر `/var/lib/marzban` قرار می‌گیرند",
    1,
)
webhook_heading = "# ارسال اعلان‌ها به آدرس وبهوک\n"
fa_node = '''# نود داخلی مرزبان

در V1.0.2، **Node Runtime V2** داخل خود مرزبان قرار دارد و دیگر به پکیج یا ایمیج جداگانه Marzban-node نیاز نیست. نود از همان ایمیج نسخه‌بندی‌شده پنل استفاده می‌کند، دیتابیس MySQL ندارد و اطلاعاتش به‌صورت جداگانه در `/opt/marzban-node` و `/var/lib/marzban-node` نگهداری می‌شود.

روی سرور نود فقط **گواهی عمومی کلاینت پنل** را به‌صورت PEM کپی کنید؛ کلید خصوصی پنل نباید روی نود قرار بگیرد. سپس نسخه دقیق را نصب کنید:

```bash
sudo bash -c "$(curl -fsSL https://raw.githubusercontent.com/smorad3363/Marzban-v1/v1.0.2/scripts/marzban.sh)" @ node install --version v1.0.2 --client-cert-file /path/to/panel-client.crt
```

دستورهای کاربردی:

```bash
marzban node status
marzban node logs
marzban node update --version v1.0.2
```

Node Runtime V2 از اعتبارسنجی سخت‌گیرانه گواهی، تحویل پایدار رویدادها و تشخیص IP بر اساس capability تأییدشده استفاده می‌کند. اگر پنل و نود روی یک سرور باشند، CLI نود در `/usr/local/bin/marzban-node` جدا نگه داشته می‌شود و آپدیت نود، CLI یا metadata نسخه پنل را بازنویسی نمی‌کند.

'''
if webhook_heading not in rf:
    raise SystemExit("README-fa.md: webhook heading not found")
rf = rf.replace(webhook_heading, fa_node + webhook_heading, 1)
readme_fa.write_text(rf, encoding="utf-8")

Path("tests/release_installer_lab.sh").write_text(r'''#!/usr/bin/env bash
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
''', encoding="utf-8")

Path("tests/release_upgrade_lab.sh").write_text(r'''#!/usr/bin/env bash
set -euo pipefail
test "${RELEASE_DISPOSABLE_LAB:-}" = 1
[[ "${RELEASE_TAG:-}" =~ ^v[0-9]+\.[0-9]+\.[0-9]+$ ]]
test "$(realpath /opt/marzban)" = /opt/marzban
test "$(realpath /var/lib/marzban)" = /var/lib/marzban
test ! -e /opt/marzban-fresh-evidence
test ! -e /var/lib/marzban-fresh-evidence
docker compose -f /opt/marzban/docker-compose.yml -p marzban down
mv /opt/marzban /opt/marzban-fresh-evidence
mv /var/lib/marzban /var/lib/marzban-fresh-evidence
mkdir -p /opt/marzban /var/lib/marzban
cp /opt/marzban-fresh-evidence/.env /opt/marzban/.env
cp /opt/marzban-fresh-evidence/docker-compose.yml /opt/marzban/docker-compose.yml
cp /var/lib/marzban-fresh-evidence/xray_config.json /var/lib/marzban/xray_config.json
baseline_commit="2d8df17b526236c9980ade37d802531dbca0d06f"
baseline_image="ghcr.io/smorad3363/marzban-vnext:v5.2.0"
baseline_build_dir="$(mktemp -d)"
mkdir -p "$baseline_build_dir/source"
curl -fsSL "https://github.com/smorad3363/Marzban-vNext/archive/${baseline_commit}.tar.gz" \
  -o "$baseline_build_dir/source.tar.gz"
tar -xzf "$baseline_build_dir/source.tar.gz" -C "$baseline_build_dir/source" --strip-components=1
docker build --pull \
  --label "org.opencontainers.image.source=https://github.com/smorad3363/Marzban-vNext" \
  --label "org.opencontainers.image.revision=${baseline_commit}" \
  --label "org.opencontainers.image.version=v5.2.0" \
  --tag "$baseline_image" \
  "$baseline_build_dir/source"
yq -i ".services.marzban.image = \"${baseline_image}\" | .services.mysql.image = \"mysql:8.0.46\" | .services.mysql.volumes = [\"/var/lib/marzban/mysql:/var/lib/mysql\"]" /opt/marzban/docker-compose.yml
docker compose -f /opt/marzban/docker-compose.yml -p marzban up -d mysql marzban
for attempt in $(seq 1 90); do
  if docker exec marzban-marzban-1 python /code/scripts/healthcheck.py --mode internal --timeout 2 >/dev/null 2>&1; then break; fi
  test "$attempt" -lt 90
  sleep 2
done
docker exec marzban-marzban-1 python -c 'from app import __version__; assert __version__ == "5.2.0"; print("BASELINE_RUNTIME", __version__)'
docker exec marzban-marzban-1 python /code/marzban-cli.py admin bootstrap-owner --username upgrade_owner --password Upgrade-Disposable-Only-927
docker exec marzban-mysql-1 sh -c 'MYSQL_PWD="$MYSQL_ROOT_PASSWORD" mysql -uroot "$MYSQL_DATABASE" -e "CREATE TABLE release_upgrade_sentinel(id INT PRIMARY KEY, value VARCHAR(64)); INSERT INTO release_upgrade_sentinel VALUES (1, '\''preserved-through-upgrade'\'');"'
export TERM=xterm
# Preserve the one-time historical product-line transition exactly as reviewed.
marzban update --version v1.0.0
bash /usr/local/bin/marzban version
require_state() {
  docker exec marzban-mysql-1 sh -c 'MYSQL_PWD="$MYSQL_ROOT_PASSWORD" mysql -uroot "$MYSQL_DATABASE" -N -e "SELECT value FROM release_upgrade_sentinel WHERE id=1; SELECT username FROM admins WHERE username='\''upgrade_owner'\''; SELECT version_num FROM alembic_version;"'
  test -d /var/lib/marzban/mysql
  test -s /opt/marzban/.mysql-migration/state
  grep -q 'phase=COMPLETE' /opt/marzban/.mysql-migration/state
  test -s /opt/marzban/backup/mysql-migration-*/marzban.sql
}
require_state

if [ "$RELEASE_TAG" != "v1.0.0" ]; then
  marzban update --version "$RELEASE_TAG"
  runtime_version="${RELEASE_TAG#v}"
  test "$(docker exec marzban-marzban-1 python -c 'from app import __version__; print(__version__)')" = "$runtime_version"
  require_state
fi

echo "UPGRADE_V520_TO_CURRENT_V1_PASS ${RELEASE_TAG}"
''', encoding="utf-8")

Path("tests/test_release_contract.py").write_text(r'''from pathlib import Path


def test_release_version_and_install_rollback_contract():
    version = Path("VERSION").read_text().strip()
    release_tag = f"v{version}"
    app = Path("app/__init__.py").read_text(encoding="utf-8")
    installer = Path("scripts/marzban.sh").read_text(encoding="utf-8")
    workflow = Path(".github/workflows/release-v1.yml").read_text()
    verify_workflow = Path(".github/workflows/verify-v1-image.yml").read_text()
    installer_workflow = Path(".github/workflows/validate-v1-installer.yml").read_text()
    build_workflow = Path(".github/workflows/build.yml").read_text()
    installer_lab = Path("tests/release_installer_lab.sh").read_text()
    upgrade_lab = Path("tests/release_upgrade_lab.sh").read_text()

    assert version == "1.0.2"
    assert f'__version__ = "{version}"' in app
    assert f'CLI_RELEASE_VERSION="{release_tag}"' in installer
    assert f"ghcr.io/smorad3363/marzban-v1:{release_tag}" in Path("docker-compose.yml").read_text()
    assert 'MARZBAN_GITHUB_REPO="${MARZBAN_GITHUB_REPO:-smorad3363/Marzban-v1}"' in installer
    assert 'MARZBAN_GITHUB_BRANCH="${MARZBAN_GITHUB_BRANCH:-main}"' in installer
    assert 'MARZBAN_DOCKER_IMAGE="${MARZBAN_DOCKER_IMAGE:-ghcr.io/smorad3363/marzban-v1}"' in installer
    assert 'V1_LINEAGE_SOURCE_VERSION="5.2.0"' in installer
    assert 'V1_LINEAGE_SOURCE_IMAGE="ghcr.io/smorad3363/marzban-vnext:v5.2.0"' in installer
    assert 'V1_LINEAGE_TARGET_VERSION="v1.0.0"' in installer
    assert "is_allowed_v1_lineage_transition()" in installer
    assert "Application downgrade refused" in installer
    assert "automatic image rollback is unsafe after migrations" in installer
    assert 'flock -n 9' in installer
    assert "Pre-update recovery snapshot" in installer
    assert 'rm -rf "$backup_dir"' not in installer
    assert 'verify_version_integrity "$marzban_version"' in installer
    assert 'verify_version_integrity "$requested_version"' in installer
    assert 'marzban_version="latest"' in installer
    assert 'requested_version="latest"' in installer
    assert 'release_commit_for_version()' in installer
    assert 'marzban_image_revision()' in installer
    assert 'record_marzban_release_revision()' in installer
    assert 'echo "Source revision: ${revision:-unavailable}"' in installer
    assert 'running_revision" = "$expected_revision' in installer
    assert '--label "org.opencontainers.image.revision=${source_commit}"' in installer
    assert 'Cached ${image} is stale or unverified; rebuilding it.' in installer
    assert 'script_ref_path="refs/heads/${script_ref}"' in installer
    assert '[[ -z "${BASH_SOURCE[0]:-}" || "${BASH_SOURCE[0]}" == "$0" ]]' in installer
    assert 'Configured MySQL image:' in installer
    assert 'Runtime MySQL version:' in installer
    assert 'create_owner_command()' in installer
    assert '-e MARZBAN_ADMIN_PASSWORD \\' in installer
    assert '-e MARZBAN_ADMIN_PASSWORD="$password"' not in installer

    assert 'Refuse overwriting an existing release image' in workflow
    assert 'org.opencontainers.image.revision' in workflow
    assert 'org.opencontainers.image.source=https://github.com/smorad3363/Marzban-v1' in workflow
    assert 'VERSION_TEXT="$(tr -d' in workflow
    assert 'test "$RELEASE_TAG" = "v${VERSION_TEXT}"' in workflow
    assert 'docs/RELEASE_NOTES_${RELEASE_TAG}.md' in workflow
    assert "vnext" not in workflow.lower()
    assert ':latest' not in workflow
    assert 'gh release create' not in workflow

    assert 'IMAGE: ghcr.io/smorad3363/marzban-v1' in verify_workflow
    assert 'release_tag:' in verify_workflow
    assert 'ref: ${{ inputs.source_commit }}' in verify_workflow
    assert 'test "$RELEASE_TAG" = "v${VERSION_TEXT}"' in verify_workflow
    assert 'test "$tagged_digest" = "$DIGEST"' in verify_workflow
    assert 'Create immutable V1 tag and stable release' in verify_workflow
    assert 'gh release create "$RELEASE_TAG"' in verify_workflow
    assert '--title "Marzban ${RELEASE_TAG}"' in verify_workflow
    assert 'docs/RELEASE_NOTES_${RELEASE_TAG}.md' in verify_workflow
    assert '--prerelease' not in verify_workflow

    assert "      - main" in build_workflow
    assert "ghcr.io/${{ github.repository_owner }}/marzban-v1" in build_workflow
    assert "github.event_name == 'workflow_dispatch'" in build_workflow
    assert 'elif [[ "${GITHUB_REF}" == "refs/heads/main" ]]' not in build_workflow
    assert 'git tag -a "${VERSION_TAG}" "${GITHUB_SHA}"' not in build_workflow

    assert 'release_tag:' in installer_workflow
    assert 'RELEASE_TAG: ${{ inputs.release_tag }}' in installer_workflow
    assert "Verify public tag, source, and anonymous image access" in installer_workflow
    assert "bash tests/release_installer_lab.sh" in installer_workflow
    assert "bash tests/release_upgrade_lab.sh" in installer_workflow
    assert "RELEASE_TAG" in installer_lab
    assert "FRESH_INSTALL_CREATE_OWNER_VERSION_PASS" in installer_lab
    assert 'marzban update --version v1.0.0' in upgrade_lab
    assert 'marzban update --version "$RELEASE_TAG"' in upgrade_lab
    assert "UPGRADE_V520_TO_CURRENT_V1_PASS" in upgrade_lab

    historical_notes = Path("docs/RELEASE_NOTES_v1.0.0.md").read_text(encoding="utf-8")
    assert "new canonical `1.0.0` product baseline" in historical_notes
    assert "Plans are commercial entitlements" in historical_notes
    assert "Access Groups exclusively own user network access" in historical_notes
    assert "Existing mature" in historical_notes

    current_notes = Path("docs/RELEASE_NOTES_v1.0.2.md").read_text(encoding="utf-8")
    assert "Built-in Node Runtime V2" in current_notes
    assert "durable" in current_notes.lower()
    assert "Access Group" in current_notes
    assert "v1.0.0" in current_notes
    assert 'readFileSync("../../VERSION", "utf8").trim()' in Path("app/dashboard/vite.config.ts").read_text()
''', encoding="utf-8")

Path("docs/RELEASE_NOTES_v1.0.2.md").write_text('''# Marzban v1.0.2

Marzban v1.0.2 keeps the V1 commercial/network ownership contract intact while adding a production-ready **Built-in Node Runtime V2** and operational hardening.

## Highlights

- Built-in Node Runtime V2 ships in the same versioned Marzban image; Nodes do not require a separate Marzban-node image or MySQL service.
- Strict certificate-based Node transport. Nodes receive only the panel client certificate used for verification; the panel private key is never copied to a Node.
- Durable SQLite-backed Node event spool with deduplication and ACK only after the panel consumes the batch, protecting usage/device events across reconnects and restarts.
- Fail-closed client-IP trust: Node IP observations are accepted only when both the configured IP-source policy and the V2 runtime capability confirm direct client-IP support.
- Node bandwidth/resource reporting and dashboard visibility for operational capacity monitoring.
- Built-in `marzban node install`, `update`, `status`, and `logs` commands with release/source-integrity checks and isolated Node state under `/opt/marzban-node` and `/var/lib/marzban-node`.
- Co-located Node CLI updates cannot overwrite the panel CLI or panel release metadata.
- Conservative runtime resource defaults and opt-in tooling profile remain suitable for smaller installations.

## Compatibility and safety

- Plans remain commercial entitlements only; Access Group ownership of Nodes, Inbounds, and Hosts is unchanged.
- The one-time mature product-line transition remains exactly `v5.2.0 -> v1.0.0`. This release does not widen that downgrade/lineage exception.
- Existing V1 installations update normally from `v1.0.0` or `v1.0.1` to `v1.0.2` through the verified release path.
- Release image publication remains immutable: an existing release tag or image is never overwritten.
''', encoding="utf-8")

state = Path("docs/CODEX/STATE.md")
s = state.read_text(encoding="utf-8")
s = s.replace("- Current branch: `main`", "- Current branch: `release/v1.0.2`", 1)
s = s.replace(
    "- Current HEAD: documentation-only V1 completion record commit containing this file",
    "- Current HEAD: V1.0.2 release-prep branch tip; exact source commit is finalized only after clean release-prep CI",
    1,
)
s = s.replace(
    "- Current milestone/checkpoint: V1 source, immutable multi-platform image, `v1.0.0` tag, stable GitHub Release, public installer, fresh-install path, Owner creation, integrity/refusal gates, and mature `v5.2.0` upgrade path are published and verified",
    "- Current milestone/checkpoint: V1.0.2 Built-in Node Runtime V2, fail-closed Node IP trust, bandwidth/resource telemetry, built-in Node deployment, CLI co-location isolation, and permanent Node deployment CI are implemented; clean feature checkpoint run `34040916354` passed all four jobs before release-prep",
    1,
)
old_next = "## NEXT EXACT TASK\n\nNONE"
new_next = '''## V1.0.2 Release-Prep Update

- Node Runtime V2 and deployment are complete, including durable event delivery, strict certificate verification, source-integrity checks, and co-located CLI isolation.
- Permanent checkpoint CI now covers panel compose, Node compose, installer contracts, MySQL 8.0, MySQL 26.7.0, Stage 8-11 evidence, and dashboard production builds.
- The V1 release publisher, image verifier, and published-installer validator are generalized to the requested release tag and must match `VERSION`.
- Historical lineage remains exactly `5.2.0 -> v1.0.0`; current release validation upgrades from that historical baseline into the requested V1 release without widening the exception.

## NEXT EXACT TASK

Run the clean V1.0.2 release-prep CI, review `main...release/v1.0.2`, then merge and publish only from the exact verified main commit.
'''
if old_next not in s:
    raise SystemExit("STATE.md: NEXT EXACT TASK marker not found")
state.write_text(s.replace(old_next, new_next, 1), encoding="utf-8")
