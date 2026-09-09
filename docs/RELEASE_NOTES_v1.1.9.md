# Marzban v1.1.9

## Highlights

- Redesign the dedicated Users Management surface into a compact, role-aware operational workspace while preserving the existing create/edit/delete/renew/enable-disable/reset/revoke/QR/Audit/Device/bulk capabilities.
- Add authorization-scoped `/api/users/summary` aggregates for total users, current activity, near-expiry users, and low-volume attention without fetching the full user set in the browser.
- Add pagination-safe `/api/users/management` filtering for Admin scope, current Plan/no-Plan/Trial, account status, expiry, usage, device-limit, inactivity, and attention signals while preserving hierarchy and inbound authorization.
- Resolve current Plan metadata from the latest immutable `UserPlanAssignment` for only the visible page, avoiding per-row Plan requests.
- Add a compact responsive table, User Details Drawer, lazy Device and Audit/Activity loading, and a sticky bulk-action surface with cross-page selection semantics preserved.
- Keep account status separate from current-activity semantics, preserve the established 24-hour Online definition, and keep Plan as commercial entitlement while Access Group remains the network-topology authority.
- Harden summary failure UX so a failed aggregate request renders an unavailable state instead of misleading real zero counts.
- Preserve Owner/Admin scope, billing confidentiality, installer safeguards, Node Runtime V2, and Panel-to-Node mTLS architecture.

## Upgrade

```bash
marzban update --version v1.1.9
```

## Fresh install

```bash
sudo bash -c "$(curl -fsSL https://raw.githubusercontent.com/smorad3363/Marzban-v1/v1.1.9/scripts/marzban.sh)" @ install --version v1.1.9 --database mysql
```

## Node Runtime

Use the same immutable release when installing or updating the built-in Node Runtime:

```bash
sudo bash -c "$(curl -fsSL https://raw.githubusercontent.com/smorad3363/Marzban-v1/v1.1.9/scripts/marzban.sh)" @ install-script v1.1.9
sudo marzban node install --version v1.1.9
```

For an existing Node installation:

```bash
sudo marzban node update --version v1.1.9
sudo marzban node doctor
```

## Validation

- Users Management backend scope, summary, pagination, Plan/no-Plan/Trial, expiry, usage, inactivity, device-limit, and attention coverage must pass on the final release source.
- Dashboard Stage 1 contracts, authenticated-autofill contract, TypeScript production build, output verification, and committed dashboard parity must pass.
- Backend regression, authorization/scope coverage, migrations/partial-DDL recovery, Stage 8-11 evidence, backup/restore, and v4.8.0 rollback compatibility must pass against MySQL 8.0 and MySQL 26.7.0.
- Installer syntax/contracts, panel compose, built-in Node compose, MySQL 8.0 logical dump -> 26.7.0 restore, release-image runtime, and Panel-to-Node mTLS contracts must pass before publication.
- The immutable `v1.1.9` tag must resolve to the exact reviewed release commit on `main`; publication must not move or recreate it.
- The canonical Release workflow must publish and anonymously verify multi-architecture `linux/amd64` and `linux/arm64` GHCR images and create the GitHub Release from this file.
