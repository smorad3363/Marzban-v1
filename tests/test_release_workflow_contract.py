from pathlib import Path


WORKFLOW_PATH = Path(".github/workflows/build.yml")


def test_release_image_verifier_uses_valid_docker_label_template() -> None:
    workflow = WORKFLOW_PATH.read_text(encoding="utf-8")
    inspect_template = (
        "docker image inspect --format "
        "'{{ index .Config.Labels \"org.opencontainers.image.revision\" }}'"
    )

    assert workflow.count(inspect_template) == 2
    assert r".Config.Labels \"org.opencontainers.image.revision\"" not in workflow


def test_release_image_verifier_reads_version_without_importing_app() -> None:
    workflow = WORKFLOW_PATH.read_text(encoding="utf-8")
    verifier = workflow.split(
        "- name: Verify published image anonymously and at runtime", 1
    )[1].split("- name: Create immutable GitHub release", 1)[0]

    assert "Path('/code/VERSION').read_text().strip()" in verifier
    assert "import app" not in verifier
    assert "from app" not in verifier
