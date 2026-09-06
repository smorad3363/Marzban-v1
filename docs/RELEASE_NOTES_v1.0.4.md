# Marzban v1.0.4

## Dashboard and administration UX

- Ports the approved enterprise/minimal admin management redesign onto the current v1 baseline.
- Adds a denser RTL user-management table so users become visible much earlier on the dashboard.
- Keeps real user/admin actions directly available, including plan renewal, enable/disable, reset usage, revoke subscription, delete, QR/subscription access, and audit navigation where the backend capability exists.
- Preserves multi-page bulk selection by username while refreshing selected users from visible page data.
- Keeps admin quick-credit actions visible and separate from destructive/freeze actions.

## Release integrity

- Preserves the v1.0.3 interactive Node certificate installer and all historical V1 lineage constraints.
- Adds the required Docker OCI source metadata, including `org.opencontainers.image.revision`, to the release image build.
- Published v1.0.0 through v1.0.3 remain unchanged.
