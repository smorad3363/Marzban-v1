# Marzban v1.0.5

This patch release ships the reviewed dashboard UX updates accumulated after v1.0.4.

## Changes

- Normalizes the Dashboard palette around shared theme tokens for consistent Light, Dark, and Black Gold rendering.
- Fixes Black Gold contrast so text remains readable on dark surfaces.
- Removes the redundant Marzban management subtitle from the welcome header.
- Restores the real Owner-only live Node bandwidth panel backed by the existing `/api/nodes/bandwidth` endpoint.
- Preserves the dense RTL Users table and its no-horizontal-scroll behavior.
- Keeps external/API-backed rotating header copy deferred; no new external API dependency is introduced.
- Preserves the existing Plan / Access Group separation and all v1.0.4 backend behavior.

## Update

Update an existing installation to the newest published stable release:

```bash
marzban update
```

Or pin this exact release:

```bash
marzban update --version v1.0.5
```

The updater creates a pre-update recovery snapshot and verifies the runtime, CLI version, source revision, image and MySQL state before reporting success.

## Fresh install

```bash
sudo bash -c "$(curl -fsSL https://raw.githubusercontent.com/smorad3363/Marzban-v1/v1.0.5/scripts/marzban.sh)" @ install --version v1.0.5 --database mysql
```

After a fresh install, create the first Owner if needed:

```bash
marzban create-owner USERNAME
```

Published v1.0.0 through v1.0.4 remain immutable and unchanged.
