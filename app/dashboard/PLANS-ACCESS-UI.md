# Plans and Access Groups UX — ui-v1.1.23

Baseline: main `a5b20c0c36013955b69da877e218a14b3aaa0438`, backend/CLI v1.1.21. Scope is frontend only. No service, context, hook, type, backend, permission policy, installer or runtime dependency changes.

## Result

- Two keyboard-accessible tabs with a URL-backed Access Groups view. Only Owner can mount network management; the existing active-account/delegated Plan guard stays unchanged.
- Searchable, category-filtered Plan catalog: compact desktop rows, mobile cards and bounded client-side pagination. Original Plan details remain in a details dialog. Category management is an on-demand dialog.
- Quick user creation opens from the selected Plan, with the same username/Access Group fields and original mutation payload. Pending, error/retry and success states retain the expected behavior.
- Access Groups show their list first. Creating/editing opens a dialog with network selection, optional Node scope, searchable Admin grants and a save summary. Search does not remove hidden selections. Existing stale-scope validation and archive blockers are retained.
- Permission summaries use the existing `admin_access_restricted` field: public legacy groups, selected Admins and Owner-only empty restrictions are distinct. Editing a legacy public group explicitly warns about the existing save semantics. No grants are added automatically.

## Validation and boundaries

`test-plans-access-ux.cjs` exercises real React Query hooks with a synthetic transport: permission summaries, filters/pagination, initially closed forms, hidden selections, unchanged payloads, duplicate-submit prevention, error/retained values/retry/success, and delegated-manager boundaries.

The native Chakra markup regression test now opens the dialog inline for SSR. It retains optional-checkbox/name-required assertions and adds optional-search and unique-label-target checks. This caught and corrected required-context inheritance on the new search/filter controls before production.

The immutable v1.1.21 behavior baseline remains intact. Exactly two presentation gestures are explicitly replaced in the boundary test: scrolling to an inline Access Group section becomes tab selection, and cancelling the inline editor becomes closing its dialog. All request/query definitions, business actions, disabled/hidden guards and select options remain checked, as do SHA256 values for 618 protected files.

KEEP: backend/API/business sources and existing Plan/Access Group options. MERGE: catalog display/search helpers and shared pagination. REPLACE: generated hashed bundles. The unused generated UserPlusIcon chunk is removed by Vite tree shaking; source/build parity checks verify the resulting graph.

Canonical build: `/home/runner/work/Marzban-v1/Marzban-v1/app/dashboard`, `VITE_BASE_API=/api/ npm run build`. Reviewed bundle SHA256: `c69bd356ff4f6ceb254afdf02952b7093aaaddf3e2ad7e784e4bd27da7d8dd46` (48 files).

Final browser acceptance, exact PR-head gates and production read-back evidence are recorded in the pull request description. Physical-phone testing is separate from browser viewport testing. Deploy only the static bundle with `scripts/deploy-ui.py`, preserving backend v1.1.21, database and environment.

The single-result browser review reproduced a clipped Plan action menu inside the scrolling table. Rendering the existing menu through Chakra Portal moves the popup outside that clipping container; all actions and handlers are preserved.
