# Marzban v1.1.7

## Highlights

- Ship Node Operations V2 as a unified operational workspace for built-in Nodes, including status, health, endpoint/version details, traffic visibility, recent events, filters, pagination, and refresh controls.
- Add durable Node event and traffic-bucket persistence with the required database migration so operational history survives process restarts.
- Add Runtime V2 structured events, health reporting, reconnect observability, and bounded Node Operations API queries.
- Add local, non-mutating `marzban node doctor` diagnostics for Node compose/configuration, certificate/key validity and expiry, ports, retention settings, container state/health, configured/running image consistency, and release-revision integrity.
- Extend built-in Node install/update/status/logs operational coverage and add Persian Node Operations/troubleshooting documentation.
- Keep the v1.1.6 Dashboard/Users split, Admin/Owner accounting visibility rules, Admin retirement behavior, Plan permissions, and Access Group ownership/network-access behavior unchanged.

## Upgrade

```bash
marzban update --version v1.1.7
```

## Fresh install

```bash
sudo bash -c "$(curl -fsSL https://raw.githubusercontent.com/smorad3363/Marzban-v1/v1.1.7/scripts/marzban.sh)" @ install --version v1.1.7 --database mysql
```

## Node Runtime

Install or update the built-in Node Runtime using the same immutable release:

```bash
sudo bash -c "$(curl -fsSL https://raw.githubusercontent.com/smorad3363/Marzban-v1/v1.1.7/scripts/marzban.sh)" @ install-script v1.1.7
sudo marzban node install --version v1.1.7
```

For an existing Node installation:

```bash
sudo marzban node update --version v1.1.7
sudo marzban node doctor
```

## Validation

- Dashboard Stage 1 UI contracts, TypeScript production build, build output, and committed dashboard parity must pass on the final release source.
- Backend regression, migrations/partial-DDL recovery, Stage 8-11 evidence, backup/restore, and v4.8.0 rollback compatibility must pass against MySQL 8.0 and MySQL 26.7.0.
- Installer syntax/contracts, panel compose, built-in Node compose, MySQL 8.0 logical dump -> 26.7.0 restore, release-image runtime, and Panel-to-Node mTLS contracts must pass before publication.
- The immutable `v1.1.7` tag must resolve to the exact reviewed release commit on `main`; publication must not move or recreate the tag.
- The canonical Release workflow must publish and anonymously verify multi-architecture `linux/amd64` and `linux/arm64` GHCR images and create the GitHub Release from this file.
