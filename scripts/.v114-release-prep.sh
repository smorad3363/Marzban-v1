#!/usr/bin/env bash
set -Eeuo pipefail

python3 - <<'PY'
from pathlib import Path

replacements = {
    Path('VERSION'): [('1.1.3\n', '1.1.4\n')],
    Path('app/__init__.py'): [('__version__ = "1.1.3"', '__version__ = "1.1.4"')],
    Path('scripts/marzban.sh'): [('CLI_RELEASE_VERSION="v1.1.3"', 'CLI_RELEASE_VERSION="v1.1.4"')],
    Path('docker-compose.yml'): [('ghcr.io/smorad3363/marzban-v1:v1.1.3', 'ghcr.io/smorad3363/marzban-v1:v1.1.4')],
}
for path, pairs in replacements.items():
    text = path.read_text()
    for old, new in pairs:
        count = text.count(old)
        if count != 1:
            raise SystemExit(f'{path}: expected exactly one {old!r}, found {count}')
        text = text.replace(old, new)
    path.write_text(text)

releases = Path('RELEASES.md')
text = releases.read_text()
old = '''## Release target: v1.1.3

v1.1.3 is the next stable release target. Complete release notes are in
`docs/RELEASE_NOTES_v1.1.3.md`.

Update to v1.1.3 after publication:

```bash
marzban update --version v1.1.3
```

Fresh-install v1.1.3 with MySQL after publication:

```bash
sudo bash -c "$(curl -fsSL https://raw.githubusercontent.com/smorad3363/Marzban-v1/v1.1.3/scripts/marzban.sh)" @ install --version v1.1.3 --database mysql
```
'''
new = '''## Release target: v1.1.4

v1.1.4 is the next stable release target. Complete release notes are in
`docs/RELEASE_NOTES_v1.1.4.md`.

Update to v1.1.4 after publication:

```bash
marzban update --version v1.1.4
```

Fresh-install v1.1.4 with MySQL after publication:

```bash
sudo bash -c "$(curl -fsSL https://raw.githubusercontent.com/smorad3363/Marzban-v1/v1.1.4/scripts/marzban.sh)" @ install --version v1.1.4 --database mysql
```
'''
if text.count(old) != 1:
    raise SystemExit('RELEASES.md v1.1.3 target block not found exactly once')
releases.write_text(text.replace(old, new))

Path('docs/RELEASE_NOTES_v1.1.4.md').write_text('''# Marzban v1.1.4

## Highlights

- Redesign the Plans page as a responsive RTL SaaS dashboard using the existing dark panel tokens with a restrained Black/Gold visual system.
- Rework Plan-category management into clear responsive cards with plan counts, inline editing, archive actions, and subtle per-category accents.
- Present Plans as premium responsive cards with prominent Persian-formatted pricing, category/trial badges, data/duration/device summaries, and localized reset-strategy labels.
- Improve the per-Plan quick-user workflow with a dedicated section while preserving the existing username, Access Group selection, and `/users/from-plan` mutation behavior.
- Reorganize the create/edit Plan modal for clearer hierarchy while retaining every existing field, Trial pricing behavior, payload structure, validation, toast, and archive flow.
- Preserve the existing `/account/summary`, `/user-plans`, `/plan-categories`, `/access-groups`, and `/users/from-plan` APIs, React Query keys, OWNER/plan-management permissions, and backend behavior unchanged.
- No database migration or backend business-logic change is introduced in v1.1.4.

## Upgrade

```bash
marzban update --version v1.1.4
```

## Fresh install

```bash
sudo bash -c "$(curl -fsSL https://raw.githubusercontent.com/smorad3363/Marzban-v1/v1.1.4/scripts/marzban.sh)" @ install --version v1.1.4 --database mysql
```

## Node Runtime

```bash
sudo bash -c "$(curl -fsSL https://raw.githubusercontent.com/smorad3363/Marzban-v1/v1.1.4/scripts/marzban.sh)" @ install-script v1.1.4
sudo marzban node install --version v1.1.4
```

## Validation

- Dashboard Stage 1 contracts, TypeScript production build, and committed source/build parity with Node.js 20.
- Full backend regression and migration/rollback evidence against MySQL 8.0 and 26.7.0.
- Installer, Panel compose, Node runtime, release-image runtime, and Panel-to-Node mTLS contracts.

This file prepares the immutable v1.1.4 release material. Publication is completed only after the reviewed commit reaches `main`, the immutable tag is created, and the canonical Release workflow verifies and publishes the multi-architecture image and GitHub Release.
''')
PY

git config user.name github-actions[bot]
git config user.email 41898282+github-actions[bot]@users.noreply.github.com
git add VERSION app/__init__.py scripts/marzban.sh docker-compose.yml RELEASES.md docs/RELEASE_NOTES_v1.1.4.md

git diff --cached --check
grep -Fx '1.1.4' VERSION
grep -Fx '__version__ = "1.1.4"' app/__init__.py
grep -Fx 'CLI_RELEASE_VERSION="v1.1.4"' scripts/marzban.sh
grep -Fq 'ghcr.io/smorad3363/marzban-v1:v1.1.4' docker-compose.yml
test -s docs/RELEASE_NOTES_v1.1.4.md

git commit -m 'release: prepare v1.1.4'
git push origin HEAD:release/v1.1.4
