from pathlib import Path


def replace_once(path: str, old: str, new: str) -> None:
    target = Path(path)
    text = target.read_text(encoding="utf-8")
    if text.count(old) != 1:
        raise SystemExit(f"expected exactly one match in {path}: {old[:80]!r}")
    target.write_text(text.replace(old, new, 1), encoding="utf-8")


release_notes = r'''# Marzban v1.0.9

This maintenance release hardens delegated administration, Access Group policy
semantics, Owner transfer safety, Node log validation, and the release/test
pipeline. It does not introduce a new database migration relative to v1.0.8.

## Permissions and dashboard contracts

- Delegated Admins with `can_manage_plans` can now open **Plans** and see the
  Plans navigation entry; Owner/sudo behavior is unchanged.
- Device Limits now uses theme tokens consistently in both Light and Dark mode.
- Dashboard source/build parity is enforced in regular CI so committed assets
  cannot silently drift from the TypeScript source.

## Access Group hardening

- Every `allowed_admin_ids` assignment is validated fail-closed for role,
  account status, hierarchy and network scope before persistence.
- Explicit `allowed_admin_ids: []` is now durable and means **deny all delegated
  Admins**, while an omitted allowlist keeps the legacy public-compatible
  behavior for older callers.
- The dashboard receives an explicit restriction flag, so an empty explicit
  policy is no longer shown as a public Access Group.

## Owner/Admin safety

- Owner transfer now normalizes the new Owner policy, keeps a demoted Owner on
  finite credit, preserves valid hierarchy parentage, and migrates Access Group
  ownership/restriction sentinels atomically.
- `SQLALCHEMY_MAX_OVERFLOW` is the canonical setting. The historical
  `SQLIALCHEMY_MAX_OVERFLOW` typo remains supported as a backward-compatible
  fallback, including Docker Compose rendering.

## Node log validation

- Node log WebSocket intervals must be numeric and satisfy `0 < interval <= 10`.
  Zero, negative, non-numeric, non-finite, and values above 10 are rejected.

## Database and release validation

- Backend regression, migration/recovery, Stage 8-11 isolated evidence,
  backup/restore, and rollback checks run on both MySQL 8.0 and MySQL 26.7.0.
- Logical MySQL 8.0 -> 26.7.0 migration remains covered.
- CI checkpoint naming is version-neutral and release-candidate Docker images are
  built without publishing on pull requests.
- The release path verifies `VERSION`, `app.__version__`, CLI version,
  Docker Compose image tag, dashboard build, and this release-notes file before
  publishing a tagged image.

## Update

Take a verified backup first, then update to the exact release:

```bash
marzban update --version v1.0.9
```

## Fresh install

```bash
sudo bash -c "$(curl -fsSL https://raw.githubusercontent.com/smorad3363/Marzban-v1/v1.0.9/scripts/marzban.sh)" @ install --version v1.0.9 --database mysql
```

## Compatibility

- Existing v1.0.8 databases do not require a new v1.0.9 schema migration.
- MySQL 8.0 and MySQL 26.7.0 remain validated release targets.
- The previous stable release remains available as immutable tag `v1.0.8`.
'''
Path("docs/RELEASE_NOTES_v1.0.9.md").write_text(release_notes, encoding="utf-8")

releases = r'''# Versioned releases and rollback

Every published release uses an immutable Git tag and permanent container tags:

- `ghcr.io/smorad3363/marzban-v1:vX.Y.Z`
- `ghcr.io/smorad3363/marzban-v1:sha-<commit-sha>`

`latest` points only to the newest stable tagged release. Older version and SHA
tags are never replaced.

## v1.0.9 release candidate

The v1.0.9 release candidate is audited but is **not published** until all version
surfaces are bumped together, the protected-main checks pass, and tag `v1.0.9` is
created from the reviewed commit.

The complete release notes are maintained in
`docs/RELEASE_NOTES_v1.0.9.md`. They cover delegated Plan permissions, Light/Dark
Device Limits, Node log interval validation, Access Group fail-closed policy,
Owner-transfer hardening, SQLAlchemy overflow compatibility, dual-MySQL evidence,
and dashboard/release pipeline parity.

## Current stable: v1.0.8

v1.0.8 is the current published stable release until v1.0.9 is tagged and its
release workflow completes.

Update to v1.0.8:

```bash
marzban update --version v1.0.8
```

Fresh-install v1.0.8 with MySQL:

```bash
sudo bash -c "$(curl -fsSL https://raw.githubusercontent.com/smorad3363/Marzban-v1/v1.0.8/scripts/marzban.sh)" @ install --version v1.0.8 --database mysql
```

Historical v1 release notes are kept under `docs/RELEASE_NOTES_v1.*.md`.

## Release process

1. Update all four version surfaces in one reviewed change: `VERSION`,
   `app.__version__`, `CLI_RELEASE_VERSION`, and the application image in
   `docker-compose.yml`.
2. Verify the matching `docs/RELEASE_NOTES_vX.Y.Z.md` exists and contains the
   actual release notes and install/update commands.
3. Merge only after the protected `main` required checks pass.
4. Create immutable tag `vX.Y.Z` from the reviewed `main` commit.
5. The tag-triggered `Release` workflow re-runs backend/migration checks, verifies
   dashboard parity and version surfaces, builds the multi-architecture image,
   publishes version/SHA tags, and creates the GitHub Release from the maintained
   notes file.
6. Verify the published digest and installer with the manual verification
   workflows. Verification never creates or moves a release tag.

## Update and install

Update to the newest stable published release:

```bash
marzban update
```

Update to an exact stable release:

```bash
marzban update --version v1.0.8
```

Fresh-install an exact release:

```bash
sudo bash -c "$(curl -fsSL https://raw.githubusercontent.com/smorad3363/Marzban-v1/v1.0.8/scripts/marzban.sh)" @ install --version v1.0.8 --database mysql
```

## Rollback

Take and verify a database backup before changing versions. Application rollback
changes the application image only; it does not automatically downgrade database
migrations.

```bash
marzban rollback v1.0.8
```

MySQL server downgrade is a separate operation and must use the physical backup
created before a MySQL upgrade; in-place MySQL downgrade is not supported.
'''
Path("RELEASES.md").write_text(releases, encoding="utf-8")

# The tag-triggered Release workflow is the sole publisher. Lock it to the
# repository version surfaces and maintained notes before any image is published.
needle = '''          echo "version_tag=${version_tag}" >> "${GITHUB_OUTPUT}"

      - name: Setup nodejs
'''
replacement = '''          echo "version_tag=${version_tag}" >> "${GITHUB_OUTPUT}"

      - name: Verify release tag, version surfaces and notes
        if: steps.release-version.outputs.version_tag != ''
        env:
          VERSION_TAG: ${{ steps.release-version.outputs.version_tag }}
        shell: bash
        run: |
          set -Eeuo pipefail
          VERSION_TEXT="$(tr -d '[:space:]' < VERSION)"
          test "${VERSION_TAG}" = "v${VERSION_TEXT}"
          grep -Fx "__version__ = \\\"${VERSION_TEXT}\\\"" app/__init__.py
          grep -Fx "CLI_RELEASE_VERSION=\\\"${VERSION_TAG}\\\"" scripts/marzban.sh
          grep -Fq "ghcr.io/smorad3363/marzban-v1:${VERSION_TAG}" docker-compose.yml
          test -s "docs/RELEASE_NOTES_${VERSION_TAG}.md"

      - name: Setup nodejs
'''
replace_once(".github/workflows/build.yml", needle, replacement)

needle = '''        run: |
          if ! gh release view "${VERSION_TAG}" >/dev/null 2>&1; then
            release_flags=()
            if [[ "${VERSION_TAG}" == *-* ]]; then
              release_flags+=(--prerelease)
            fi
            gh release create "${VERSION_TAG}" \\
              --title "Marzban ${VERSION_TAG}" \\
              --generate-notes \\
              --verify-tag \\
              "${release_flags[@]}"
          fi
'''
replacement = '''        run: |
          set -Eeuo pipefail
          NOTES_FILE="docs/RELEASE_NOTES_${VERSION_TAG}.md"
          test -s "${NOTES_FILE}"
          if ! gh release view "${VERSION_TAG}" >/dev/null 2>&1; then
            release_flags=()
            if [[ "${VERSION_TAG}" == *-* ]]; then
              release_flags+=(--prerelease)
            fi
            gh release create "${VERSION_TAG}" \\
              --title "Marzban ${VERSION_TAG}" \\
              --notes-file "${NOTES_FILE}" \\
              --verify-tag \\
              "${release_flags[@]}"
          fi
'''
replace_once(".github/workflows/build.yml", needle, replacement)

# Remove stale v1.0.2 defaults from post-publication verification workflows.
for path in (
    ".github/workflows/validate-v1-installer.yml",
    ".github/workflows/verify-v1-image.yml",
):
    text = Path(path).read_text(encoding="utf-8")
    if text.count("        default: v1.0.2\n") != 1:
        raise SystemExit(f"stale default count changed in {path}")
    Path(path).write_text(text.replace("        default: v1.0.2\n", "", 1), encoding="utf-8")

# Verification must be read-only: tagging/release creation belongs only to build.yml.
replace_once(
    ".github/workflows/verify-v1-image.yml",
    "permissions:\n  contents: write\n  packages: read\n",
    "permissions:\n  contents: read\n  packages: read\n",
)
verify_path = Path(".github/workflows/verify-v1-image.yml")
verify_text = verify_path.read_text(encoding="utf-8")
marker = "      - name: Create immutable V1 tag and stable release\n"
if verify_text.count(marker) != 1:
    raise SystemExit("expected exactly one release-creation step in verify workflow")
verify_path.write_text(verify_text.split(marker, 1)[0].rstrip() + "\n", encoding="utf-8")

# Obsolete manual publisher: build.yml is now the only publishing workflow.
legacy_publisher = Path(".github/workflows/release-v1.yml")
if not legacy_publisher.exists():
    raise SystemExit("expected legacy release-v1.yml before Stage 10 cleanup")
legacy_publisher.unlink()

# Add a non-publishing Docker build/runtime smoke check to PR/manual checkpoints.
checkpoints = Path(".github/workflows/checkpoints.yml")
checkpoints_text = checkpoints.read_text(encoding="utf-8")
if "  docker-smoke:\n" in checkpoints_text:
    raise SystemExit("docker-smoke already exists")
checkpoints_text = checkpoints_text.rstrip() + r'''

  docker-smoke:
    name: docker image smoke
    if: ${{ github.event_name == 'pull_request' || github.event_name == 'workflow_dispatch' }}
    runs-on: ubuntu-latest
    steps:
      - uses: actions/checkout@v4
      - name: Build release image without publishing
        run: docker build --tag marzban-v1:ci .
      - name: Verify release image runtime contract
        shell: bash
        run: |
          set -Eeuo pipefail
          version="$(tr -d '[:space:]' < VERSION)"
          runtime_version="$(docker run --rm --entrypoint python \
            -e SQLALCHEMY_DATABASE_URL=mysql+pymysql://probe:probe@127.0.0.1/probe \
            marzban-v1:ci -c 'from app import __version__; print(__version__)')"
          test "${runtime_version}" = "${version}"
          docker run --rm --entrypoint mysqldump marzban-v1:ci --version | grep -q 'Ver 26.7.0'
          docker run --rm --entrypoint sh marzban-v1:ci -c \
            'test -s /code/app/dashboard/build/index.html && \
             test -s /code/app/dashboard/build/404.html && \
             test -x /usr/bin/marzban-cli && \
             test -f /code/node_runtime/main.py'
''' + "\n"
checkpoints.write_text(checkpoints_text, encoding="utf-8")

release_contract = r'''import re
from pathlib import Path


def test_release_version_and_install_rollback_contract():
    version = Path("VERSION").read_text().strip()
    release_tag = f"v{version}"
    app = Path("app/__init__.py").read_text(encoding="utf-8")
    installer = Path("scripts/marzban.sh").read_text(encoding="utf-8")
    verify_workflow = Path(".github/workflows/verify-v1-image.yml").read_text()
    installer_workflow = Path(".github/workflows/validate-v1-installer.yml").read_text()
    build_workflow = Path(".github/workflows/build.yml").read_text()
    checkpoints = Path(".github/workflows/checkpoints.yml").read_text()
    installer_lab = Path("tests/release_installer_lab.sh").read_text()
    upgrade_lab = Path("tests/release_upgrade_lab.sh").read_text()

    assert re.fullmatch(r"\d+\.\d+\.\d+", version)
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

    assert not Path(".github/workflows/release-v1.yml").exists()
    assert "      - main" in build_workflow
    assert "ghcr.io/${{ github.repository_owner }}/marzban-v1" in build_workflow
    assert "github.event_name == 'workflow_dispatch'" in build_workflow
    assert 'elif [[ "${GITHUB_REF}" == "refs/heads/main" ]]' not in build_workflow
    assert 'git tag -a "${VERSION_TAG}" "${GITHUB_SHA}"' not in build_workflow
    assert "Verify release tag, version surfaces and notes" in build_workflow
    assert 'docs/RELEASE_NOTES_${VERSION_TAG}.md' in build_workflow
    assert '--notes-file "${NOTES_FILE}"' in build_workflow
    assert "--generate-notes" not in build_workflow

    assert 'IMAGE: ghcr.io/smorad3363/marzban-v1' in verify_workflow
    assert 'release_tag:' in verify_workflow
    assert 'ref: ${{ inputs.source_commit }}' in verify_workflow
    assert 'test "$RELEASE_TAG" = "v${VERSION_TEXT}"' in verify_workflow
    assert 'test "$tagged_digest" = "$DIGEST"' in verify_workflow
    assert "contents: read" in verify_workflow
    assert "Create immutable V1 tag and stable release" not in verify_workflow
    assert "gh release create" not in verify_workflow
    assert "git tag -a" not in verify_workflow
    assert "default: v1.0.2" not in verify_workflow

    assert 'release_tag:' in installer_workflow
    assert 'RELEASE_TAG: ${{ inputs.release_tag }}' in installer_workflow
    assert "Verify public tag, source, and anonymous image access" in installer_workflow
    assert "bash tests/release_installer_lab.sh" in installer_workflow
    assert "bash tests/release_upgrade_lab.sh" in installer_workflow
    assert "default: v1.0.2" not in installer_workflow
    assert "RELEASE_TAG" in installer_lab
    assert "FRESH_INSTALL_CREATE_OWNER_VERSION_PASS" in installer_lab
    assert 'marzban update --version v1.0.0' in upgrade_lab
    assert 'marzban update --version "$RELEASE_TAG"' in upgrade_lab
    assert "UPGRADE_V520_TO_CURRENT_V1_PASS" in upgrade_lab

    assert "docker image smoke" in checkpoints
    assert "docker build --tag marzban-v1:ci ." in checkpoints
    assert "Build release image without publishing" in checkpoints

    historical_notes = Path("docs/RELEASE_NOTES_v1.0.0.md").read_text(encoding="utf-8")
    assert "new canonical `1.0.0` product baseline" in historical_notes
    assert "Plans are commercial entitlements" in historical_notes
    assert "Access Groups exclusively own user network access" in historical_notes
    assert "Existing mature" in historical_notes

    current_notes = Path(f"docs/RELEASE_NOTES_{release_tag}.md").read_text(encoding="utf-8")
    assert "dashboard" in current_notes.lower()
    assert "access group" in current_notes.lower()
    assert "marzban update" in current_notes
    assert 'readFileSync("../../VERSION", "utf8").trim()' in Path("app/dashboard/vite.config.ts").read_text()


def test_v109_release_candidate_material_is_real_and_repository_scoped():
    notes = Path("docs/RELEASE_NOTES_v1.0.9.md").read_text(encoding="utf-8")
    releases = Path("RELEASES.md").read_text(encoding="utf-8")

    for phrase in (
        "can_manage_plans",
        "0 < interval <= 10",
        "explicit",
        "Owner transfer",
        "SQLALCHEMY_MAX_OVERFLOW",
        "MySQL 26.7.0",
        "marzban update --version v1.0.9",
    ):
        assert phrase.lower() in notes.lower()

    assert "v1.0.9 release candidate" in releases
    assert "Current stable: v1.0.8" in releases
    assert "docs/RELEASE_NOTES_v1.0.9.md" in releases
    assert "## v5." not in releases
    assert "## v4." not in releases
'''
Path("tests/test_release_contract.py").write_text(release_contract, encoding="utf-8")

print("Stage 10 reconciliation prepared")
