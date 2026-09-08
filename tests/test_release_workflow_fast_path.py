from pathlib import Path


ROOT = Path(__file__).resolve().parents[1]
WORKFLOW = (ROOT / ".github" / "workflows" / "build.yml").read_text(encoding="utf-8")
TRIGGER = (ROOT / ".github" / "workflows" / "release-v1.1.1-trigger.yml").read_text(encoding="utf-8")


def test_release_publish_path_uses_canonical_dashboard_contract_only():
    assert "node scripts/test-stage1-ui-contracts.cjs" in WORKFLOW
    assert "node scripts/test-admin-ux.cjs" not in WORKFLOW
    assert "node scripts/test-access-groups.cjs" not in WORKFLOW
    assert "node scripts/test-v106-ui.cjs" not in WORKFLOW


def test_release_publish_path_does_not_repeat_heavy_mysql_ci():
    assert "test-mysql (" not in WORKFLOW
    assert "test-mysql logical migration" not in WORKFLOW
    assert "pytest" not in WORKFLOW


def test_release_publish_path_keeps_safety_gates_and_cache():
    for marker in (
        "git merge-base --is-ancestor",
        "CLI_RELEASE_VERSION",
        "RELEASE_NOTES_",
        "git diff --exit-code -- app/dashboard/build",
        "linux/amd64,linux/arm64",
        "cache-from: type=gha",
        "cache-to: type=gha,mode=max",
        "Verify published image anonymously and at runtime",
        "Create immutable GitHub release",
    ):
        assert marker in WORKFLOW


def test_release_workflow_no_longer_runs_on_every_main_push():
    on_block = WORKFLOW.split("permissions:", 1)[0]
    assert "branches:" not in on_block
    assert 'tags:' in on_block
    assert 'workflow_dispatch:' in on_block


def test_v111_trigger_is_idempotent_without_retagging():
    assert "tag_exists=true" in TRIGGER
    assert "tag_commit" in TRIGGER
    assert "steps.release-target.outputs.tag_exists != 'true'" in TRIGGER
    assert 'gh workflow run build.yml' in TRIGGER
