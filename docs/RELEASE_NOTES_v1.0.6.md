# Marzban v1.0.6

## Access Groups and admin scope

- Access Group is now the explicit network-access scope used by both plan-based and free-form user creation.
- Owner can restrict an Access Group to selected admins; the API enforces the same permission server-side instead of relying on UI filtering.
- Admins only see groups they can actually use, including the existing inbound ceiling as defense in depth.
- Changing a user's owner revalidates the assigned Access Group, closing a permission bypass through ownership transfer.
- Existing Access Groups without explicit admin assignments remain compatible as shared groups.
- Access Group management moved out of generic Settings and into the Plans area, next to the commercial plan workflow while remaining technically independent from plan pricing/limits.

## Dashboard UI/UX

- The dashboard now has exactly two appearance modes: Light and Dark. The old blue/gold theme axis is no longer exposed.
- Light and Dark use a single tokenized palette for backgrounds, surfaces, sidebar, borders, text, primary actions, and semantic status colors.
- Cards, dialogs, controls, and buttons use a consistent 12–16px radius system and subtle borders/shadows.
- Tables have more breathing room, low-contrast zebra rows instead of row separators, quieter headers, and clearer disabled rows.
- User status is rendered as a soft outlined badge with a status dot.
- Traffic usage now includes a thin progress indicator; unlimited users retain a distinct infinity indicator.
- The users toolbar uses compact segmented status filters plus a collapsible advanced filter area beside search.
- The three common row actions remain direct (copy, edit, delete); all other existing actions remain available from the overflow menu.
- Admin management keeps the current hierarchy, billing, quota, and permission capabilities while adopting the unified visual system.
- The former Settings navigation entry is presented as Configuration; no operational option was removed.

## Upgrade

Existing V1 installations can update with:

```bash
marzban update
```

After updating, run `marzban version` to verify the CLI, application version, Docker image, digest, and MySQL runtime.
