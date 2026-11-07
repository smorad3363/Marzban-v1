# Quiet alert center — ui-v1.1.24

Baseline: main `c9bac04fba4c0351b44560327bae4f3a8bdd3eef`, backend/CLI v1.1.21. Frontend scope only.

## Interaction

- One existing summary query and authenticated event stream serve a compact bell in the persistent workspace bar. Its badge counts all active incidents, including seen incidents. Unknown/stale delivery and inherited restrictions remain distinguishable.
- The full list opens on demand in a focus-managed Chakra Drawer. It uses the full mobile width, one scrollable body, grouped Admin names, compact incident summaries, expandable original numeric details, the existing seen action, filters and pagination. Delivery diagnostics are collapsed by default.
- Only the dashboard includes a bounded summary of up to three active incidents from the current page. Healthy pages show no empty banner. Large-result summaries explicitly identify the list as recent records, rather than promising global priority across API pages.
- Toasts announce only unseen active critical incidents whose revision has not already been announced for that viewer. Resolutions, removals, warnings and unchanged refreshes stay quiet. A critical reopened/worsened revision can announce again. Local receipts persist across reloads and are bounded to 256 ID/revision pairs per viewer; storage failures fall back to memory. The backend remains authoritative for seen, active and resolved state.
- Seeing an incident does not resolve it or remove it from active counts. Existing Owner/all and Admin/self-and-descendant scope is retained; the UI adds no grants and does not filter away backend-authorized incidents. Only Owner receives the management navigation link.
- Drawer movement uses transform-only motion with a reduced-motion override. Optional details and filters open without decorative motion. Theme tokens, readable labels, keyboard focus return, 44px primary touch targets, safe footer padding and long-name wrapping use existing primitives.

## Boundaries and validation

KEEP: all backend/API/business sources, role guards, event transport/reconnect, query keys/request URLs/polling intervals, receipt POST and every existing filter/option. The immutable behavior baseline is unchanged. The boundary test explicitly permits only the summary query's presentation-only `onSuccess: announce` replacement and compares the rest of that query exactly. A separate AST hash guard protects the original stream effect and seen operation.

MERGE: the compact trigger, dashboard summary and Drawer share one query owner through the shell. Pure presentation/notification helpers live in `src/components/alerts/presentation.ts`.

REPLACE: generated hashed frontend bundles; old unreachable hashed files are removed only through the canonical Vite build and parity checks. No runtime dependency or backend version is added or changed.

`test-alert-center.cjs` verifies persistent, per-viewer critical notification receipts, reload, escalation, resolution, seen state, malformed/unavailable storage, unchanged transport, real React Query refresh/receipt failure/retry, filters, pagination, inherited restrictions, healthy states and closed-panel behavior. It runs inside the existing UI CI gate. Browser acceptance and exact-head production evidence are recorded in the pull request. Physical-device testing is not implied by browser viewport testing.

Browser review reproduced inherited mobile modal margins pushing the full-height Drawer footer below the viewport. The alert Drawer alone explicitly resets its margin, uses viewport width on mobile and keeps its header/footer from shrinking. Shared modal styles remain unchanged.
