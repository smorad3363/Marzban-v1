from pathlib import Path

VERSION = "1.0.6"
TAG = f"v{VERSION}"

Path("VERSION").write_text(VERSION + "\n", encoding="utf-8")

p = Path("app/__init__.py")
s = p.read_text(encoding="utf-8")
s = s.replace('__version__ = "1.0.5"', f'__version__ = "{VERSION}"')
p.write_text(s, encoding="utf-8")

p = Path("scripts/marzban.sh")
s = p.read_text(encoding="utf-8")
s = s.replace('CLI_RELEASE_VERSION="v1.0.5"', f'CLI_RELEASE_VERSION="{TAG}"')
p.write_text(s, encoding="utf-8")

p = Path("docker-compose.yml")
s = p.read_text(encoding="utf-8")
s = s.replace('ghcr.io/smorad3363/marzban-v1:v1.0.5', f'ghcr.io/smorad3363/marzban-v1:{TAG}')
p.write_text(s, encoding="utf-8")

p = Path("tests/test_release_contract.py")
s = p.read_text(encoding="utf-8")
s = s.replace('assert version == "1.0.5"', f'assert version == "{VERSION}"')
s = s.replace('Path("docs/RELEASE_NOTES_v1.0.5.md")', f'Path("docs/RELEASE_NOTES_{TAG}.md")')
s = s.replace('assert "node" in current_notes.lower()\n    assert "marzban update" in current_notes', 'assert "access group" in current_notes.lower()\n    assert "light" in current_notes.lower() and "dark" in current_notes.lower()\n    assert "marzban update" in current_notes')
p.write_text(s, encoding="utf-8")

p = Path("tests/test_installer_v1_contract.sh")
s = p.read_text(encoding="utf-8").replace("v1.0.5", TAG).replace("1.0.5", VERSION)
p.write_text(s, encoding="utf-8")

# Public docs should point at the release being prepared instead of the older pinned example.
for name in ("README.md", "README-fa.md"):
    p = Path(name)
    s = p.read_text(encoding="utf-8")
    s = s.replace("v1.0.3/scripts/marzban.sh", f"{TAG}/scripts/marzban.sh")
    s = s.replace("--version v1.0.3", f"--version {TAG}")
    p.write_text(s, encoding="utf-8")

notes = f'''# Marzban {TAG}

## Access Groups and admin scope

- Access Group is now the explicit network-access scope used by both plan-based and free-form user creation.
- Owner can restrict an Access Group to selected admins; the API enforces the same permission server-side instead of relying on UI filtering.
- Admins only see groups they can actually use, including the existing inbound ceiling as defense in depth.
- Changing a user's owner revalidates the assigned Access Group, closing a permission bypass through ownership transfer.
- Existing Access Groups without explicit admin assignments remain compatible as shared groups.
- Access Group management moved out of generic Settings and into the Plans area, next to the commercial plan workflow while remaining technically independent from plan pricing/limits.

## Dashboard UI/UX

- The dashboard now has exactly two appearance modes: Light and Dark. The old blue/gold theme axis is no longer exposed.
- Light and Dark use a single tokenized palette for backgrounds, surfaces, sidebar, borders, text, primary actions, and semantic status colors.
- Cards, dialogs, controls, and buttons use a consistent 12–16px radius system and subtle borders/shadows.
- Tables have more breathing room, low-contrast zebra rows instead of row separators, quieter headers, and clearer disabled rows.
- User status is rendered as a soft outlined badge with a status dot.
- Traffic usage now includes a thin progress indicator; unlimited users retain a distinct infinity indicator.
- The users toolbar uses compact segmented status filters plus a collapsible advanced filter area beside search.
- The three common row actions remain direct (copy, edit, delete); all other existing actions remain available from the overflow menu.
- Admin management keeps the current hierarchy, billing, quota, and permission capabilities while adopting the unified visual system.
- The former Settings navigation entry is presented as Configuration; no operational option was removed.

## Upgrade

Existing V1 installations can update with:

```bash
marzban update
```

After updating, run `marzban version` to verify the CLI, application version, Docker image, digest, and MySQL runtime.
'''
Path(f"docs/RELEASE_NOTES_{TAG}.md").write_text(notes, encoding="utf-8")

print(f"release metadata prepared for {TAG}")
