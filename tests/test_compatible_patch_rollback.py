import json
import shutil
import subprocess
import tempfile
import unittest
from pathlib import Path

SCRIPT = Path(__file__).resolve().parents[1] / "scripts/marzban.sh"


class CompatiblePatchRollbackTests(unittest.TestCase):
    def run_probe(self, current="1.1.25", target="v1.1.24", equal=True, fail=False):
        digest = "a" * 64
        other = digest if equal else "b" * 64
        shell = f'''source "{SCRIPT}"
marzban_docker_image() {{ echo test-image; }}
ensure_marzban_image() {{ return 0; }}
docker() {{
    if [ "$1" = exec ]; then echo {digest};
    else {'return 1' if fail else f'echo {other}'}; fi
}}
compatible_patch_rollback "{current}" "{target}" current-container
'''
        return subprocess.run(["bash", "-c", shell], capture_output=True, text=True)

    def test_qualified_pair_with_identical_migrations_is_allowed(self):
        self.assertEqual(self.run_probe().returncode, 0)

    def test_changed_or_unreadable_schema_is_rejected(self):
        self.assertNotEqual(self.run_probe(equal=False).returncode, 0)
        self.assertNotEqual(self.run_probe(fail=True).returncode, 0)

    def test_arbitrary_rollback_is_rejected(self):
        self.assertNotEqual(self.run_probe(target="v1.1.23").returncode, 0)
        self.assertNotEqual(self.run_probe(current="1.2.0").returncode, 0)

    @unittest.skipUnless(shutil.which("yq"), "real yq is required for Compose parsing")
    def test_only_dashboard_mounts_are_removed(self):
        volumes = ["/data:/var/lib/marzban", "/old-ui:/code/app/dashboard/build:ro",
                   {"type": "bind", "source": "/old-ui-2", "target": "/code/app/dashboard/build", "read_only": True},
                   {"type": "bind", "source": "/custom", "target": "/custom"}, "/env:/opt/marzban/.env:ro"]
        with tempfile.TemporaryDirectory() as folder:
            compose = Path(folder) / "compose.json"
            compose.write_text(json.dumps({"services": {"marzban": {"volumes": volumes}}}))
            result = subprocess.run(["bash", "-c", f'source "{SCRIPT}"; COMPOSE_FILE="{compose}"; remove_frontend_override'], capture_output=True, text=True)
            self.assertEqual(result.returncode, 0, result.stderr)
            actual = subprocess.check_output(["yq", "-o=json", ".services.marzban.volumes", str(compose)], text=True)
            self.assertEqual(json.loads(actual), [volumes[0], volumes[3], volumes[4]])

    def test_backup_precedes_override_removal(self):
        body = SCRIPT.read_text().split("update_command() {", 1)[1].split("update_marzban_script() {", 1)[0]
        self.assertLess(body.index('cp "$COMPOSE_FILE" "$ENV_FILE"'), body.index("remove_frontend_override || exit 1"))
        self.assertLess(body.index('compatible_patch_rollback "$current_version"'), body.index('stop marzban'))
