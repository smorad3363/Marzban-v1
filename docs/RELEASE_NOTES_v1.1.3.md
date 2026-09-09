# Marzban v1.1.3

## Highlights

- Replace hard Admin deletion with logical retirement so immutable billing and audit-history foreign keys remain valid instead of surfacing generic database conflicts.
- Allow Access Group permission revocation to block future assignment while preserving existing user bindings; existing bindings still obey the owning Admin inbound/network ceiling.
- Persist Admin Plan-category grants on create and edit, and preserve existing Plan grants when editing Plans.
- Let `FORM_ONLY` (custom-form) Admins receive Plan-category access and load their available Plan list without enabling Plan-based user creation; `/users/from-plan` remains forbidden for that creation mode.
- Add focused backend, MySQL, and Dashboard regression coverage for Admin retirement, Access Group revocation, Plan-category visibility, and the custom-form Plan-access UI.
- Add migration `e7b1c4d9a213` for nullable indexed `admins.deleted_at` used by Admin retirement.

## Upgrade

```bash
marzban update --version v1.1.3
```

## Fresh install

```bash
sudo bash -c "$(curl -fsSL https://raw.githubusercontent.com/smorad3363/Marzban-v1/v1.1.3/scripts/marzban.sh)" @ install --version v1.1.3 --database mysql
```

## Node Runtime

```bash
sudo bash -c "$(curl -fsSL https://raw.githubusercontent.com/smorad3363/Marzban-v1/v1.1.3/scripts/marzban.sh)" @ install-script v1.1.3
sudo marzban node install --version v1.1.3
```

## Validation

- Full backend regression suite against MySQL 8.0 and 26.7.0, including migration and rollback/recovery contracts.
- Dashboard type-check/build plus committed source/build parity with Node.js 20.
- Installer, Panel compose, Node runtime, image runtime, Access Group, Admin hierarchy, and release-version contracts.

This file prepares the immutable v1.1.3 release material. Publication is completed only after the reviewed commit reaches `main`, the immutable tag is created, and the tag-triggered Release workflow verifies and publishes the multi-architecture image and GitHub Release.
