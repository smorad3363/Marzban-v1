from pathlib import Path


def replace_once(path: str, old: str, new: str) -> None:
    file_path = Path(path)
    text = file_path.read_text()
    count = text.count(old)
    if count != 1:
        raise SystemExit(f"{path}: expected exactly one {old!r}, found {count}")
    file_path.write_text(text.replace(old, new, 1))


Path("VERSION").write_text("1.1.3\n")
replace_once("app/__init__.py", '__version__ = "1.1.2"', '__version__ = "1.1.3"')
replace_once(
    "scripts/marzban.sh",
    'CLI_RELEASE_VERSION="v1.1.2"',
    'CLI_RELEASE_VERSION="v1.1.3"',
)
replace_once(
    "docker-compose.yml",
    "ghcr.io/smorad3363/marzban-v1:v1.1.2",
    "ghcr.io/smorad3363/marzban-v1:v1.1.3",
)

releases_path = Path("RELEASES.md")
releases = releases_path.read_text()
if releases.count("v1.1.2") < 4:
    raise SystemExit("RELEASES.md: unexpected v1.1.2 target section")
releases_path.write_text(releases.replace("v1.1.2", "v1.1.3"))

Path("docs/RELEASE_NOTES_v1.1.3.md").write_text(
    """# Marzban v1.1.3

## Highlights

- Replace hard Admin deletion with logical retirement so immutable billing and audit-history foreign keys remain valid instead of surfacing generic database conflicts.
- Allow Access Group permission revocation to block future assignment while preserving existing user bindings; existing bindings still obey the owning Admin inbound/network ceiling.
- Persist Admin Plan-category grants on create and edit, and preserve existing Plan grants when editing Plans.
- Let `FORM_ONLY` (custom-form) Admins receive Plan-category access and load their available Plan list without enabling Plan-based user creation; `/users/from-plan` remains forbidden for that creation mode.
- Add focused backend, MySQL, and Dashboard regression coverage for Admin retirement, Access Group revocation, Plan-category visibility, and the custom-form Plan-access UI.
- Add migration `e7b1c4d9a213` for nullable indexed `admins.deleted_at` used by Admin retirement.

## Upgrade

```bash
marzban update --version v1.1.3
```

## Fresh install

```bash
sudo bash -c "$(curl -fsSL https://raw.githubusercontent.com/smorad3363/Marzban-v1/v1.1.3/scripts/marzban.sh)" @ install --version v1.1.3 --database mysql
```

## Node Runtime

```bash
sudo bash -c "$(curl -fsSL https://raw.githubusercontent.com/smorad3363/Marzban-v1/v1.1.3/scripts/marzban.sh)" @ install-script v1.1.3
sudo marzban node install --version v1.1.3
```

## Validation

- Full backend regression suite against MySQL 8.0 and 26.7.0, including migration and rollback/recovery contracts.
- Dashboard type-check/build plus committed source/build parity with Node.js 20.
- Installer, Panel compose, Node runtime, image runtime, Access Group, Admin hierarchy, and release-version contracts.

This file prepares the immutable v1.1.3 release material. Publication is completed only after the reviewed commit reaches `main`, the immutable tag is created, and the tag-triggered Release workflow verifies and publishes the multi-architecture image and GitHub Release.
"""
)

assert Path("VERSION").read_text().strip() == "1.1.3"
assert '__version__ = "1.1.3"' in Path("app/__init__.py").read_text()
assert 'CLI_RELEASE_VERSION="v1.1.3"' in Path("scripts/marzban.sh").read_text()
assert "ghcr.io/smorad3363/marzban-v1:v1.1.3" in Path("docker-compose.yml").read_text()
assert "## Release target: v1.1.3" in Path("RELEASES.md").read_text()
assert Path("docs/RELEASE_NOTES_v1.1.3.md").stat().st_size > 0
