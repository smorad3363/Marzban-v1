# Marzban v1.1.6

## Highlights

- Separate the main Dashboard from user management: `/` is now the role-aware overview and `/users/` is the dedicated Users workspace.
- For delegated Admin accounts, the Dashboard now shows only the account's own operational information such as financial credit, credit limit/usage/remaining balance, owned users, subtree users, trial allowance, and remaining Admin-creation capacity.
- Do not expose the Admin's commercial calculation label on the self Dashboard; the UI does not reveal whether the account is based on consumed traffic, allocated/created traffic, or plan/account credit.
- For Owner accounts, the Dashboard focuses on Admin-management information instead of showing Owner credit/account-limit cards.
- Exclude the authenticated Admin/Owner identity from Admin list responses at the backend query/count layer, so self rows do not consume pagination or appear in Admin management lists.
- Keep Owner/Admin hierarchy permissions, Admin deletion/retirement behavior from v1.1.5, Plan permissions, and existing Access Group ownership/network-access behavior unchanged.
- Add regression coverage for Admin-list self exclusion and Stage 1 UI contracts for the Dashboard/Users split and hidden commercial-mode labels.
- This release introduces no new database migration; existing v1.1.5 account, billing, Plan, Access Group, audit, and retirement data remain compatible.

## Upgrade

```bash
marzban update --version v1.1.6
```

## Fresh install

```bash
sudo bash -c "$(curl -fsSL https://raw.githubusercontent.com/smorad3363/Marzban-v1/v1.1.6/scripts/marzban.sh)" @ install --version v1.1.6 --database mysql
```

## Node Runtime

```bash
sudo bash -c "$(curl -fsSL https://raw.githubusercontent.com/smorad3363/Marzban-v1/v1.1.6/scripts/marzban.sh)" @ install-script v1.1.6
sudo marzban node install --version v1.1.6
```

## Validation

- Dashboard Stage 1 contracts must verify the dedicated `/users/` route, the absence of embedded user management from the main Dashboard, and the absence of commercial calculation labels from the Admin self Dashboard.
- TypeScript production build and committed dashboard source/build parity must pass on the final release commit using `VITE_BASE_API=/api/`.
- Backend regression, migrations/partial-DDL recovery, Stage 8-11 evidence, backup/restore, and rollback compatibility must pass against MySQL 8.0 and MySQL 26.7.0.
- Installer, Panel compose, release-image runtime, and Panel-to-Node mTLS contracts must pass before publication.
- The immutable `v1.1.6` tag must resolve to the exact reviewed merge commit on `main`; publication must not move or recreate the tag.

This file prepares the immutable v1.1.6 release material. Publication is complete only after the reviewed release commit reaches `main`, the immutable `v1.1.6` tag is created from that commit, and the canonical Release workflow verifies and publishes the multi-architecture image and GitHub Release.
