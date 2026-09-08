import re
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
    node_e2e = Path("tests/node_panel_e2e.sh").read_text(encoding="utf-8")

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
    release_on_block = build_workflow.split("permissions:", 1)[0]
    assert "branches:" not in release_on_block
    assert "tags:" in release_on_block
    assert "workflow_dispatch:" in release_on_block
    assert "ghcr.io/${{ github.repository_owner }}/marzban-v1" in build_workflow
    assert 'elif [[ "${GITHUB_REF}" == "refs/heads/main" ]]' not in build_workflow
    assert 'git tag -a "${VERSION_TAG}" "${GITHUB_SHA}"' not in build_workflow
    assert "Verify release tag, protected-main ancestry, version surfaces and notes" in build_workflow
    assert "fetch-depth: 0" in build_workflow
    assert 'git fetch --no-tags origin main' in build_workflow
    assert 'tag_commit="$(git rev-list -n 1 "${VERSION_TAG}")"' in build_workflow
    assert 'git merge-base --is-ancestor "${tag_commit}" origin/main' in build_workflow
    assert 'docs/RELEASE_NOTES_${VERSION_TAG}.md' in build_workflow
    assert '--notes-file "${notes_file}"' in build_workflow
    assert "--generate-notes" not in build_workflow

    verifier_section = build_workflow.split("- name: Verify published image anonymously and at runtime", 1)[1]
    verifier_section = verifier_section.split("- name: Create immutable GitHub release", 1)[0]
    assert "import app" not in verifier_section
    assert "Path('/code/VERSION').read_text().strip()" in verifier_section

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

    assert "name: dashboard build and parity" in checkpoints
    assert "Verify Stage 1 UI contracts" in checkpoints
    assert "node scripts/test-stage1-ui-contracts.cjs" in checkpoints
    assert "name: installer, panel compose and node contracts" in checkpoints
    assert "docker build --tag marzban-v1:ci ." in checkpoints
    assert "Build release image without publishing" in checkpoints
    assert "Verify release image runtime contract" in checkpoints
    assert "Verify Panel-to-Node mTLS end-to-end" in checkpoints
    assert "bash tests/node_panel_e2e.sh marzban-v1:ci" in checkpoints
    assert "\n  docker-smoke:" not in checkpoints

    assert "V2ReSTXRayNode" in node_e2e
    assert "/v2/handshake" in node_e2e
    assert "node.connect()" in node_e2e
    assert "node.connected" in node_e2e
    assert "PANEL_NODE_MTLS_E2E_PASS" in node_e2e
    assert "node-data/panel-client.key" in node_e2e

    historical_notes = Path("docs/RELEASE_NOTES_v1.0.0.md").read_text(encoding="utf-8")
    assert "new canonical `1.0.0` product baseline" in historical_notes
    assert "Plans are commercial entitlements" in historical_notes
    assert "Access Groups exclusively own user network access" in historical_notes
    assert "Existing mature" in historical_notes

    current_notes = Path(f"docs/RELEASE_NOTES_{release_tag}.md").read_text(encoding="utf-8")
    assert "dashboard" in current_notes.lower()
    assert "access group" in current_notes.lower()
    assert "marzban update" in current_notes
    releases = Path("RELEASES.md").read_text(encoding="utf-8")
    assert f"Release target: {release_tag}" in releases or f"Current stable: {release_tag}" in releases
    assert f"docs/RELEASE_NOTES_{release_tag}.md" in releases
    assert 'readFileSync("../../VERSION", "utf8").trim()' in Path("app/dashboard/vite.config.ts").read_text()


def test_v109_release_material_is_real_and_repository_scoped():
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

    assert "v1.0.9" in releases
    assert "immutable" in releases.lower()
    assert "## v5." not in releases
    assert "## v4." not in releases
