# v1.1.21

Admin creation and editing now display an explicit loading label while saving. The header and footer do not shrink; only the form body scrolls. The create action is labelled Create Admin rather than Save changes.

Validation and API errors stay visible above the submit action and preserve the entered values for correction. Duplicate submission and dismissal are blocked while a save is pending. The request has a 30-second timeout and no automatic retry. The form closes only after a successful response; the existing list and capability refreshes remain in place. If the response is lost, check the Admin list before retrying, since the server may already have completed the operation.

A component regression uses the real React Query mutation/cache hooks and Chakra button to exercise pending submission, duplicate-submit protection, an API failure, retained values, deliberate retry and successful closure. Both dashboard CI jobs run this test.

No database migration, accounting, permission, Access Group, network or Node runtime change is included. Generated dashboard assets and synchronized release version surfaces are updated for publication. Historical assets, migrations and attribution are retained; superseded generated dashboard bundles are replaced by the canonical build.

Run the exact-head MySQL 8.0/26.7.0, installer/Node mTLS and dashboard gates before publication. Verify the immutable published image and installer before the separately authorized server update. The installer takes a private recovery snapshot and preserves the existing local-core configuration.

Update command: `marzban update --version v1.1.21`.
