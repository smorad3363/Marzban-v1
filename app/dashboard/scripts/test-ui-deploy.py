import importlib.util
from pathlib import Path
import unittest

spec = importlib.util.spec_from_file_location("deploy_ui", Path(__file__).with_name("deploy-ui.py"))
deploy = importlib.util.module_from_spec(spec)
spec.loader.exec_module(deploy)


class FrontendDeploymentTests(unittest.TestCase):
    def test_preserves_every_existing_setting(self):
        source = "services:\n  marzban:\n    image: pinned-image\n    env_file: .env\n    volumes:\n      - /var/lib/marzban:/var/lib/marzban\n      - /opt/marzban/.env:/opt/marzban/.env:ro\n    network_mode: host\n  mysql:\n    image: mysql:26.7.0\n    volumes:\n      - db:/var/lib/mysql\n"
        target = Path("/opt/marzban/frontend-releases/test/build")
        result = deploy.mount_frontend(source, target)
        addition = f"      - {target}:/code/app/dashboard/build:ro\n"
        self.assertEqual(result.replace(addition, ""), source)
        self.assertEqual(deploy.mount_frontend(result, target), result)

    def test_replaces_only_the_previous_ui_mount(self):
        source = "services:\n  marzban:\n    volumes:\n      - /old/build:/code/app/dashboard/build:ro\n      - data:/var/lib/marzban\n"
        result = deploy.mount_frontend(source, Path("/new/build"))
        self.assertNotIn("/old/build", result)
        self.assertIn("      - data:/var/lib/marzban\n", result)
        self.assertEqual(result.count(":/code/app/dashboard/build:ro"), 1)

    def test_refuses_ambiguous_compose(self):
        for source in ["services: {}", "services:\n  marzban:\n    volumes: [data]\n", "services:\n  other:\n    volumes:\n      - data:/var/lib/marzban\n"]:
            with self.assertRaises(ValueError):
                deploy.mount_frontend(source, Path("/new/build"))


if __name__ == "__main__":
    unittest.main()
