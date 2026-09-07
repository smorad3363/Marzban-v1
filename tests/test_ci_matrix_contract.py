from pathlib import Path


RELEASE_WORKFLOW = Path(".github/workflows/build.yml")
CHECKPOINTS_WORKFLOW = Path(".github/workflows/checkpoints.yml")
DASHBOARD_WORKFLOW = Path(".github/workflows/dashboard-ui-contracts.yml")
STAGE9_TEST = Path("tests/test_mysql_stage9_dashboard.py")
STAGE10_TEST = Path("tests/test_mysql_stage10_pagination.py")


def _read(path: Path) -> str:
    return path.read_text(encoding="utf-8")


def test_stage8_11_mysql_evidence_runs_on_both_matrix_images():
    for path in (RELEASE_WORKFLOW, CHECKPOINTS_WORKFLOW):
        text = _read(path)
        assert "mysql:8.0" in text
        assert "mysql:26.7.0" in text
        assert "matrix.mysql-image == 'mysql:8.0'" not in text
        assert 'matrix.mysql-image == "mysql:8.0"' not in text
        assert 'mysql:8.0) expected_mysql_version_prefix="8.0."' in text
        assert 'mysql:26.7.0) expected_mysql_version_prefix="26.7."' in text
        assert 'TEST_MYSQL_VERSION_PREFIX="${expected_mysql_version_prefix}"' in text
        assert "Unsupported MySQL matrix image" in text
        for stage_test in (
            "tests/test_mysql_stage8_bulk_jobs.py",
            "tests/test_mysql_stage9_dashboard.py",
            "tests/test_mysql_stage10_pagination.py",
            "tests/test_mysql_stage11_operations.py",
        ):
            assert stage_test in text


def test_stage9_10_server_version_checks_are_matrix_driven():
    for path in (STAGE9_TEST, STAGE10_TEST):
        text = _read(path)
        assert 'os.getenv("TEST_MYSQL_VERSION_PREFIX", "8.0.")' in text
        assert '.startswith("8.0.")' not in text


def test_release_matrix_keeps_migration_backup_and_rollback_checks():
    text = _read(RELEASE_WORKFLOW)
    assert "Verify MySQL migrations and partial-DDL recovery" in text
    assert "Verify backup checksum and restore" in text
    assert "Verify v4.8.0 application rollback compatibility" in text
    assert "Verify 8.0 logical dump and 26.7.0 restore" in text


def test_dashboard_source_build_parity_is_enforced_in_permanent_workflows():
    for path in (RELEASE_WORKFLOW, CHECKPOINTS_WORKFLOW, DASHBOARD_WORKFLOW):
        text = _read(path)
        assert "VITE_BASE_API=/api/ npm run build" in text
        assert "git diff --exit-code -- app/dashboard/build" in text
        assert "--outDir /tmp/marzban-dashboard-build" not in text
        assert "app/dashboard/build/index.html" in text
        assert "app/dashboard/build/404.html" in text
