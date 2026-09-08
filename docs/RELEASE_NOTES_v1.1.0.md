# Marzban v1.1.0

## Highlights

- Fix Admin user creation from Plan by loading the Admin-scoped available Plan list instead of the Owner-only Plan-management endpoint.
- Add an explicit Admin user-creation selector: **Form only**, **Plan only**, or **Both**. `USER_CREDIT` remains Plan-only by backend contract.
- Preserve billing semantics: `USED_TRAFFIC` charges real usage by the Admin per-GiB rate; `ALLOCATED_TRAFFIC` Plan purchases charge the effective Plan price.
- Harden the permanent Release workflow for immutable tag-source dispatch and anonymous runtime verification.

## Upgrade

```bash
marzban update --version v1.1.0
```

## Fresh install

```bash
sudo bash -c "$(curl -fsSL https://raw.githubusercontent.com/smorad3363/Marzban-v1/v1.1.0/scripts/marzban.sh)" @ install --version v1.1.0 --database mysql
```

The existing `v1.0.9` tag remains unchanged.
