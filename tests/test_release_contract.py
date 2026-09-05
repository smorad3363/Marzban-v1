import re
from pathlib import Path


def test_release_version_and_install_rollback_contract():
    version = Path("VERSION").read_text().strip()
    app = Path("app/__init__.py").read_text(encoding="utf-8")
    installer = Path("scripts/marzban.sh").read_text(encoding="utf-8")
    workflow = Path(".github/workflows/release-v1.yml").read_text()
    verify_workflow = Path(".github/workflows/verify-v1-image.yml").read_text()
    installer_workflow = Path(".github/workflows/validate-v1-installer.yml").read_text()
    build_workflow = Path(".github/workflows/build.yml").read_text()
    assert version == "1.0.0"
    assert f'__version__ = "{version}"' in app
    assert f'CLI_RELEASE_VERSION="v{version}"' in installer
    assert f"ghcr.io/smorad3363/marzban-v1:v{version}" in Path("docker-compose.yml").read_text()
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
    assert 'install_marzban_script_from_repo "$marzban_version" "$MARZBAN_GITHUB_BRANCH"' in installer
    assert 'update_marzban_script "$requested_version" "$MARZBAN_GITHUB_BRANCH"' in installer
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
    assert 'IMAGE: ghcr.io/smorad3363/marzban-v1' in verify_workflow
    assert '= 1.0.0' in verify_workflow
    assert "      - main" in build_workflow
    assert "ghcr.io/${{ github.repository_owner }}/marzban-v1" in build_workflow
    assert "vnext" not in workflow.lower()
    assert "vnext" not in verify_workflow.lower()
    assert ':latest' not in workflow
    assert 'gh release create' not in workflow  # Publish notes only after runtime verification.
    assert "github.event_name == 'workflow_dispatch'" in build_workflow
    assert 'elif [[ "${GITHUB_REF}" == "refs/heads/main" ]]' not in build_workflow
    assert 'git tag -a "${VERSION_TAG}" "${GITHUB_SHA}"' not in build_workflow
    assert 'ref: ${{ inputs.source_commit }}' in verify_workflow
    assert 'test "$tagged_digest" = "$DIGEST"' in verify_workflow
    assert 'Create immutable V1 tag and stable release' in verify_workflow
    assert 'gh release create "$RELEASE_TAG"' in verify_workflow
    assert '--title "Marzban V1.0.0"' in verify_workflow
    assert '--notes-file docs/RELEASE_NOTES_v1.0.0.md' in verify_workflow
    assert '--prerelease' not in verify_workflow
    assert "Verify public tag, source, and anonymous image access" in installer_workflow
    assert "bash tests/release_installer_lab.sh" in installer_workflow
    assert "bash tests/release_upgrade_lab.sh" in installer_workflow
    assert "FRESH_INSTALL_CREATE_OWNER_VERSION_PASS" in Path("tests/release_installer_lab.sh").read_text()
    assert "UPGRADE_V520_TO_V100_PASS" in Path("tests/release_upgrade_lab.sh").read_text()
    release_notes = Path("docs/RELEASE_NOTES_v1.0.0.md").read_text(encoding="utf-8")
    assert "new canonical `1.0.0` product baseline" in release_notes
    assert "Plans are commercial entitlements" in release_notes
    assert "Access Groups exclusively own user network access" in release_notes
    assert "Existing mature" in release_notes
    assert 'readFileSync("../../VERSION", "utf8").trim()' in Path("app/dashboard/vite.config.ts").read_text()
