# Marzban v1.1.1

## Highlights

- Make the Dashboard Users table usable on mobile and tablet with controlled horizontal scrolling, readable non-wrapping headers, and preserved bulk/action behavior.
- Restore canonical Admin billing choices for Owner/Sudo creation: used traffic, allocated traffic, and Plan-only account credit (`USER_CREDIT`) without changing billing semantics.
- Align delegated Admin manual user creation with Owner-defined duration presets and positive traffic requirements, while preserving the existing Plan creation path and Access Group authorization semantics.
- Fix Owner/Sudo Admin deletion authorization when legacy role metadata is stale, while keeping child-admin, unsettled-credit, immutable billing-history, and audit-history protections intact and surfacing structured Persian failure reasons.
- Fix updater service-state detection so stopped/exited containers are not treated as running, improve runtime-version diagnostics, and ensure update/rollback recovery brings the target service back up.
- Normalize Dashboard/API failures into actionable safe errors with machine error code, Persian message, affected field when known, HTTP status, and request tracking ID without exposing database or traceback details.
- Make the published-image release verifier DB-independent by reading `/code/VERSION` directly instead of importing the full application.
- Rebuild and lock Dashboard source/build parity and keep release contracts covered by CI on MySQL 8.0 and MySQL 26.7.0.

## Upgrade

```bash
marzban update --version v1.1.1
```

## Fresh install

```bash
sudo bash -c "$(curl -fsSL https://raw.githubusercontent.com/smorad3363/Marzban-v1/v1.1.1/scripts/marzban.sh)" @ install --version v1.1.1 --database mysql
```

This file prepares the immutable v1.1.1 release material only. Creating the Git tag, GitHub Release, versioned container image, or moving `latest` is a separate publication step.
