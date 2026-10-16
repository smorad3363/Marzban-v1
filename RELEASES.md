# Marzban V1 — Immutable Releases

Verified stable Release: [v1.1.9](https://github.com/smorad3363/Marzban-v1/releases/tag/v1.1.9) (2026-09-09).

## Release target: v1.1.10 (NOT PUBLISHED)

New maintenance patch candidate only. See `docs/RELEASE_NOTES_v1.1.10.md`, [STATE](docs/STATE.md) and [RELEASE](docs/RELEASE.md). Historic tags/images/Release notes (including v1.0.9, v1.1.7, v1.1.8, v1.1.9) remain unchanged; only successfully published stable release owns `latest`.

Immutable images: `ghcr.io/smorad3363/marzban-v1:vX.Y.Z` and `ghcr.io/smorad3363/marzban-v1:sha-<short-source-sha>`.

After verified publication:
```bash
marzban update --version v1.1.10
sudo bash -c "$(curl -fsSL https://raw.githubusercontent.com/smorad3363/Marzban-v1/v1.1.10/scripts/marzban.sh)" @ install --version v1.1.10 --database mysql
```
