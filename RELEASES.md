# v1.1.18

Release target: v1.1.18

Fix Admin wallet persistence, legacy debt recovery, duration coefficients and Trial management. [Notes](docs/RELEASE_NOTES_v1.1.18.md).

# v1.1.17

Release target: v1.1.17

Reconcile removed core Inbounds with Access Groups and add explicit tag rename. [Notes](docs/RELEASE_NOTES_v1.1.17.md).

# v1.1.16

Release target: v1.1.16

Preserve Owner exemption in financial ancestor checks. [Notes](docs/RELEASE_NOTES_v1.1.16.md).

# v1.1.15

Release target: v1.1.15

Deletion purchase refunds, direct-parent decisions, debt controls and Plan renewal. [Notes](docs/RELEASE_NOTES_v1.1.15.md).

# v1.1.14

Release target: v1.1.14

Explicit Access Group network synchronization. [Notes](docs/RELEASE_NOTES_v1.1.14.md).

# v1.1.13

Release target: v1.1.13

Access Group navigation and delegated permission refresh. [Notes](docs/RELEASE_NOTES_v1.1.13.md).

# v1.1.12

Release target: v1.1.12

Host editor and Access Group refresh fixes. See [release notes](docs/RELEASE_NOTES_v1.1.12.md).

# v1.1.11

Release target: v1.1.11

Safety fixes and unified latest-stable installer. See [release notes](docs/RELEASE_NOTES_v1.1.11.md). Real traffic qualification remains pending.

# Marzban V1 — Immutable Releases

Current stable: v1.1.10. Latest **verified stable Release**: [v1.1.10](https://github.com/smorad3363/Marzban-v1/releases/tag/v1.1.10) (published 2026-10-16). Source commit: `b09801ca922199b06eaf43938664544331328668`.

Release notes: [v1.1.10](docs/RELEASE_NOTES_v1.1.10.md).

Published multi-arch image: `ghcr.io/smorad3363/marzban-v1:v1.1.10`, digest `sha256:2b37aefc1b37a2e3f6c27489e69ca323f34e5aa3c00ff2e51c55c59361f5bb8f`. Both published-image verification and disposable fresh installation **PASS**; see [STATE](docs/STATE.md), [TESTING](docs/TESTING.md) and [RELEASE](docs/RELEASE.md).

Prior stable [v1.1.9](https://github.com/smorad3363/Marzban-v1/releases/tag/v1.1.9) and older tags/images (including historical v1.0.9, v1.1.7 and v1.1.8) remain unchanged. Immutable image names use `ghcr.io/smorad3363/marzban-v1:vX.Y.Z` and `ghcr.io/smorad3363/marzban-v1:sha-<short-source-sha>`.

```bash
marzban update --version v1.1.10
sudo bash -c "$(curl -fsSL https://raw.githubusercontent.com/smorad3363/Marzban-v1/v1.1.10/scripts/marzban.sh)" @ install --version v1.1.10 --database mysql
```
