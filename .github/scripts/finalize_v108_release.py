from pathlib import Path


def replace(path: str, old: str, new: str) -> None:
    p = Path(path)
    text = p.read_text(encoding="utf-8")
    if old not in text:
        if new in text:
            return
        raise SystemExit(f"missing expected marker in {path}: {old!r}")
    p.write_text(text.replace(old, new, 1), encoding="utf-8")

replace(
    "scripts/marzban.sh",
    'CLI_RELEASE_VERSION="v1.0.7"',
    'CLI_RELEASE_VERSION="v1.0.8"',
)
replace(
    "tests/test_release_contract.py",
    '    assert version == "1.0.7"',
    '    assert version == "1.0.8"',
)
replace(
    "tests/test_release_contract.py",
    '    current_notes = Path("docs/RELEASE_NOTES_v1.0.7.md").read_text(encoding="utf-8")',
    '    current_notes = Path(f"docs/RELEASE_NOTES_{release_tag}.md").read_text(encoding="utf-8")',
)

notes = Path("docs/RELEASE_NOTES_v1.0.8.md")
notes.write_text("""# Marzban v1.0.8

This maintenance release focuses on dashboard UI reliability while preserving the
backend, Access Group authorization model, Admin hierarchy, Plan behavior, and
Node management introduced in the previous releases.

## Dashboard and navigation fixes

- Bulk User operations are condensed into compact **Status**, **Credit**, and
  **Cleanup** menus. Activate/deactivate, data adjustments, day adjustments,
  combined data+days, cleanup, and delete remain available; no operation was
  removed.
- The **Light** theme now explicitly applies the light navigation/sidebar palette,
  while the **Dark** theme keeps the approved dark palette.
- Core, Host, Node, and Node usage configuration dialogs are mounted at the
  shared application shell, so they work from Users, Plans, Admins, Audit Logs,
  Device Limits, and Settings instead of only the Dashboard route.
- The **Reset all usage** shortcut was removed from the configuration navigation.
- Modal close buttons are kept above editor/header controls and remain directly
  clickable.
- The rotating dashboard status slogan was removed.
- Default `Operations Console` / `Operations workspace` sidebar branding and the
  fallback logo are hidden when no custom branding is configured.

## Compatibility

- Access Group permissions and Plan/Free Form Access Group selection remain
  unchanged.
- Existing Node Management behavior is preserved.
- MySQL 8.0 and MySQL 26.7.0 remain covered by the release workflow, including
  logical migration and rollback compatibility checks.

## Update

```bash
marzban update --version v1.0.8
```

## Fresh install

```bash
sudo bash -c "$(curl -fsSL https://raw.githubusercontent.com/smorad3363/Marzban-v1/v1.0.8/scripts/marzban.sh)" @ install --version v1.0.8 --database mysql
```
""", encoding="utf-8")

app = Path("app/__init__.py").read_text(encoding="utf-8")
if '__version__ = "1.0.8"' not in app:
    raise SystemExit("app version was not bumped to 1.0.8")

print("v1.0.8 release metadata finalized")
