# Versioned releases and rollback

Every published release uses an immutable Git tag and permanent container tags:

- `ghcr.io/smorad3363/marzban-v1:vX.Y.Z`
- `ghcr.io/smorad3363/marzban-v1:sha-<commit-sha>`

`latest` points only to the newest stable tagged release. Older version and SHA
tags are never replaced.

## Release target: v1.1.9

v1.1.9 is the next stable release target. Complete release notes are in
`docs/RELEASE_NOTES_v1.1.9.md`.

Update to v1.1.9 after publication:

```bash
marzban update --version v1.1.9
```

Fresh-install v1.1.9 with MySQL after publication:

```bash
sudo bash -c "$(curl -fsSL https://raw.githubusercontent.com/smorad3363/Marzban-v1/v1.1.9/scripts/marzban.sh)" @ install --version v1.1.9 --database mysql
```

The existing `v1.1.7` and `v1.1.8` source tags remain immutable, and all previously published tags and releases remain unchanged. Preparing this target does not create or move any tag or container alias.

## Release process

1. Update all four version surfaces in one reviewed change: `VERSION`,
   `app.__version__`, `CLI_RELEASE_VERSION`, and the application image in
   `docker-compose.yml`.
2. Verify the matching `docs/RELEASE_NOTES_vX.Y.Z.md` exists and contains the
   actual release notes and install/update commands.
3. Merge only after the protected `main` required checks pass.
4. Create immutable tag `vX.Y.Z` from the reviewed `main` commit.
5. The tag-triggered `Release` workflow re-runs backend/migration checks, verifies
   dashboard parity and version surfaces, builds the multi-architecture image,
   publishes version/SHA tags, and creates the GitHub Release from the maintained
   notes file.
6. Verify the published digest and installer with the manual verification
   workflows. Verification never creates or moves a release tag.

## Update and install

Update to the newest stable published release:

```bash
marzban update
```

Update to an exact stable release:

```bash
marzban update --version v1.1.9
```

Fresh-install an exact release:

```bash
sudo bash -c "$(curl -fsSL https://raw.githubusercontent.com/smorad3363/Marzban-v1/v1.1.9/scripts/marzban.sh)" @ install --version v1.1.9 --database mysql
```

## Rollback

Take and verify a database backup before changing versions. Application rollback
changes the application image only; it does not automatically downgrade database
migrations.

```bash
marzban rollback v1.1.8
```

MySQL server downgrade is a separate operation and must use the physical backup
created before a MySQL upgrade; in-place MySQL downgrade is not supported.
