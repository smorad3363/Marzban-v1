from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]


def replace(path: str, old: str, new: str) -> None:
    target = ROOT / path
    text = target.read_text(encoding="utf-8")
    if old not in text:
        raise SystemExit(f"missing expected release-prep pattern in {path}: {old!r}")
    target.write_text(text.replace(old, new), encoding="utf-8")


(ROOT / "VERSION").write_text("1.1.6\n", encoding="utf-8")
replace("app/__init__.py", '__version__ = "1.1.5"', '__version__ = "1.1.6"')
replace("scripts/marzban.sh", 'CLI_RELEASE_VERSION="v1.1.5"', 'CLI_RELEASE_VERSION="v1.1.6"')
replace("docker-compose.yml", 'ghcr.io/smorad3363/marzban-v1:v1.1.5', 'ghcr.io/smorad3363/marzban-v1:v1.1.6')
replace("RELEASES.md", "v1.1.5", "v1.1.6")

notes = ROOT / "docs/RELEASE_NOTES_v1.1.6.md"
if not notes.exists():
    raise SystemExit("v1.1.6 release notes are missing")

print("v1.1.6 release surfaces prepared")
