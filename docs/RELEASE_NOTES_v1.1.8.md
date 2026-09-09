# Marzban v1.1.8

## Highlights

- Redesign the Dashboard as separate role-aware Owner and Admin operational views backed only by real scoped backend aggregates; the dedicated Users page remains the full user-management surface.
- Add real 24-hour, 7-day, and 30-day user-traffic history from the existing authoritative usage collector, current-activity counts, status distribution, attention signals, top consumers, and recent-user summaries without adding a second Xray polling path.
- Add Owner-only compact Node and Admin summaries while keeping Admin data restricted to its authorized user scope in the backend.
- Keep Admin credit presentation generic and avoid exposing billing-model basis; Owner remains unrestricted.
- Prevent saved login credentials from autofilling authenticated/non-login inputs, including dynamically mounted Chakra portals, while preserving username/current-password autofill on the Login page.
- Extend Dashboard UI contracts, backend authorization/scope tests, and the canonical Release workflow so the autofill invariant and committed dashboard parity are verified before publication.
- Preserve Node Operations V2, safe Admin retirement, Plan permissions, Access Group semantics, and existing installer/mTLS architecture.

## Upgrade

```bash
marzban update --version v1.1.8
```

## Fresh install

```bash
sudo bash -c "$(curl -fsSL https://raw.githubusercontent.com/smorad3363/Marzban-v1/v1.1.8/scripts/marzban.sh)" @ install --version v1.1.8 --database mysql
```

## Node Runtime

Use the same immutable release when installing or updating the built-in Node Runtime:

```bash
sudo bash -c "$(curl -fsSL https://raw.githubusercontent.com/smorad3363/Marzban-v1/v1.1.8/scripts/marzban.sh)" @ install-script v1.1.8
sudo marzban node install --version v1.1.8
```

For an existing Node installation:

```bash
sudo marzban node update --version v1.1.8
sudo marzban node doctor
```

## Validation

- Dashboard Stage 1 contracts, authenticated-autofill contract, TypeScript production build, output verification, and committed dashboard parity must pass on the final release source.
- Backend regression, authorization/scope coverage, migrations/partial-DDL recovery, Stage 8-11 evidence, backup/restore, and v4.8.0 rollback compatibility must pass against MySQL 8.0 and MySQL 26.7.0.
- Installer syntax/contracts, panel compose, built-in Node compose, MySQL 8.0 logical dump -> 26.7.0 restore, release-image runtime, and Panel-to-Node mTLS contracts must pass before publication.
- The immutable `v1.1.8` tag must resolve to the exact reviewed release commit on `main`; publication must not move or recreate it.
- The canonical Release workflow must publish and anonymously verify multi-architecture `linux/amd64` and `linux/arm64` GHCR images and create the GitHub Release from this file.
