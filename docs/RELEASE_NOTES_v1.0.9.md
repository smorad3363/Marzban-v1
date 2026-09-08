# Marzban v1.0.9

This maintenance release hardens delegated administration, Access Group policy
semantics, Owner transfer safety, Node log validation, and the release/test
pipeline. It does not introduce a new database migration relative to v1.0.8.

## Permissions and dashboard contracts

- Delegated Admins with `can_manage_plans` can now open **Plans** and see the
  Plans navigation entry; Owner/sudo behavior is unchanged.
- Device Limits now uses theme tokens consistently in both Light and Dark mode.
- Dashboard source/build parity is enforced in regular CI so committed assets
  cannot silently drift from the TypeScript source.
- v1.0.9 dashboard assets were regenerated from the reviewed release source
  before tagging.

## Access Group hardening

- Every `allowed_admin_ids` assignment is validated fail-closed for role,
  account status, hierarchy and network scope before persistence.
- Explicit `allowed_admin_ids: []` is now durable and means **deny all delegated
  Admins**, while an omitted allowlist keeps the legacy public-compatible
  behavior for older callers.
- The dashboard receives an explicit restriction flag, so an empty explicit
  policy is no longer shown as a public Access Group.

## Owner/Admin safety

- Owner transfer now normalizes the new Owner policy, keeps a demoted Owner on
  finite credit, preserves valid hierarchy parentage, and migrates Access Group
  ownership/restriction sentinels atomically.
- `SQLALCHEMY_MAX_OVERFLOW` is the canonical setting. The historical
  `SQLIALCHEMY_MAX_OVERFLOW` typo remains supported as a backward-compatible
  fallback, including Docker Compose rendering.

## Node log validation

- Node log WebSocket intervals must be numeric and satisfy `0 < interval <= 10`.
  Zero, negative, non-numeric, non-finite, and values above 10 are rejected.

## Database and release validation

- Backend regression, migration/recovery, Stage 8-11 isolated evidence,
  backup/restore, and rollback checks run on both MySQL 8.0 and MySQL 26.7.0.
- Logical MySQL 8.0 -> 26.7.0 migration remains covered.
- CI checkpoint naming is version-neutral and release-candidate Docker images are
  built without publishing on pull requests.
- A real Panel-to-Node mTLS end-to-end gate verifies client-certificate
  enforcement, v2 handshake, connect/ping/status/disconnect, and private-key isolation.
- The release path verifies `VERSION`, `app.__version__`, CLI version,
  Docker Compose image tag, dashboard build, and this release-notes file before
  publishing a tagged image.

## Update

Take a verified backup first, then update to the exact release:

```bash
marzban update --version v1.0.9
```

## Fresh install

```bash
sudo bash -c "$(curl -fsSL https://raw.githubusercontent.com/smorad3363/Marzban-v1/v1.0.9/scripts/marzban.sh)" @ install --version v1.0.9 --database mysql
```

## Compatibility

- Existing v1.0.8 databases do not require a new v1.0.9 schema migration.
- MySQL 8.0 and MySQL 26.7.0 remain validated release targets.
- The previous stable release remains available as immutable tag `v1.0.8`.
