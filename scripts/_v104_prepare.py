from pathlib import Path


def replace_required(path: str, old: str, new: str) -> None:
    p = Path(path)
    text = p.read_text(encoding="utf-8")
    if old not in text:
        raise SystemExit(f"expected text not found in {path}: {old!r}")
    p.write_text(text.replace(old, new), encoding="utf-8")


# Focused UI build fixes found by the TypeScript gate.
replace_required(
    "app/dashboard/src/pages/Admins.tsx",
    'export { AdminsPage as Admins } from "./admins/AdminsPage";\nexport { default } from "./admins/AdminsPage";\n',
    'export { AdminsPage as Admins } from "./admins/AdminsPage";\n',
)
replace_required("app/dashboard/src/components/UsersTablePro.tsx", "  LinkSlashIcon,\n", "  LinkIcon,\n")
replace_required("app/dashboard/src/components/UsersTablePro.tsx", "chakra(LinkSlashIcon,", "chakra(LinkIcon,")
replace_required(
    "app/dashboard/src/components/UsersTablePro.tsx",
    '      onError: (error) => toast({ title: "تمدید انجام نشد", description: localizedApiError(error), status: "error", duration: 5000 }),\n',
    '      onError: (error) => {\n        toast({ title: "تمدید انجام نشد", description: localizedApiError(error), status: "error", duration: 5000 });\n      },\n',
)

# Preserve fail-closed operator guidance from the existing Admin page.
replace_required(
    "app/dashboard/src/pages/admins/AdminsPage.tsx",
    '<Text mt={1} fontSize="sm">تا فعال‌سازی، مدیریت سلسله‌مراتب و بعضی دسترسی‌ها محدود است.</Text>',
    '<Text mt={1} fontSize="sm">تا فعال‌سازی، مدیریت سلسله‌مراتب و بعضی دسترسی‌ها محدود است.</Text>\n              <Text mt={2} fontSize="sm">Use command-line administration to promote an Owner.</Text>',
)

# The Admin page was intentionally refactored into a wrapper, page and table.
# Keep security/authorization assertions, and update only assertions tied to the approved UX.
ux_path = Path("app/dashboard/scripts/test-admin-ux.cjs")
ux = ux_path.read_text(encoding="utf-8")
ux = ux.replace(
    'const admins = read("src/pages/Admins.tsx");',
    'const admins = [\n  read("src/pages/Admins.tsx"),\n  read("src/pages/admins/AdminsPage.tsx"),\n  read("src/pages/admins/AdminTable.tsx"),\n].join("\\n");',
)
replacements = {
    'assert.ok(admins.includes("colSpan={4}"), "Admin desktop list must stay limited to four purposeful data groups");':
        'assert.ok(admins.includes("colSpan={7}") && admins.includes("عملیات سریع"), "Admin desktop list must keep the approved dense operational columns");',
    'assert.ok(admins.includes("statusMeta[item.account_status].background"), "Admin rows must expose status with both text and a distinct surface");':
        'assert.ok(admins.includes("<StatusPill status={item.account_status} />"), "Admin rows must expose status with a distinct semantic surface");',
    'assert.ok(admins.includes("کیف پول تومان") && admins.includes("money_balance_toman"), "Admin summary must show the monetary wallet");':
        'assert.ok(admins.includes("کیف پول") && admins.includes("money_balance_toman"), "Admin summary must show the monetary wallet");',
    'assert.ok(admins.includes("renderMoreActions(item, true)"), "mobile Admin cards must keep secondary actions in a compact accessible menu");':
        'assert.ok(admins.includes("onEdit(item)") && admins.includes("onStatus(item)") && admins.includes("onDelete(item)"), "Admin cards must keep edit, status and delete as direct real actions");',
    'assert.ok(admins.includes("فیلتر نوع اعتبار"), "Admin list must expose billing-mode filtering");':
        'assert.ok(admins.includes("نوع اعتبار:") && admins.includes("setBillingFilter"), "Admin list must expose billing-mode filtering");',
    'assert.ok(admins.includes("زیرمجموعهٔ:"), "Admin relationship label must describe the child relationship");':
        'assert.ok(admins.includes("parent_username") && admins.includes("والد"), "Admin relationship must expose the parent relationship");',
    'assert.ok(admins.includes(\'openCredit(item, "grant")\'), "Admin rows must expose quick credit grant beside status actions");':
        'assert.ok(admins.includes(\'onCredit(item, "grant")\'), "Admin rows must expose direct quick credit grant beside the amount field");',
    'assert.ok(admins.includes(\'openCredit(item, "reclaim")\'), "Admin rows must expose quick credit reclaim beside status actions");':
        'assert.ok(admins.includes(\'onCredit(item, "reclaim")\'), "Admin rows must expose direct quick credit reclaim beside the amount field");',
    'assert.ok(admins.includes("filtersDisclosure.onToggle"), "Admin filters must be collapsed by default");':
        'assert.ok(admins.includes("<FilterButton") && !admins.includes("filtersDisclosure"), "approved Admin status and billing filters must stay directly visible");',
    'assert.ok(!settings.includes(\'fetch("/owner/backups/restore"\') && settings.includes("Online restore is disabled"), "UI must honor offline-only recovery");':
        'assert.ok(!settings.includes(\'fetch("/owner/backups/restore"\') && settings.includes("بازیابی آنلاین برای حفاظت از داده فعال غیرفعال است"), "UI must honor offline-only recovery");',
}
for old, new in replacements.items():
    if old not in ux:
        raise SystemExit(f"admin UX assertion not found: {old}")
    ux = ux.replace(old, new)
ux_path.write_text(ux, encoding="utf-8")

# v1.0.4 source/version contract.
Path("VERSION").write_text("1.0.4\n", encoding="utf-8")
replace_required("app/__init__.py", '__version__ = "1.0.3"', '__version__ = "1.0.4"')
replace_required("docker-compose.yml", 'ghcr.io/smorad3363/marzban-v1:v1.0.3', 'ghcr.io/smorad3363/marzban-v1:v1.0.4')
replace_required("scripts/marzban.sh", 'CLI_RELEASE_VERSION="v1.0.3"', 'CLI_RELEASE_VERSION="v1.0.4"')

p = Path("tests/test_installer_v1_contract.sh")
text = p.read_text(encoding="utf-8")
p.write_text(text.replace("v1.0.3", "v1.0.4").replace("1.0.3", "1.0.4"), encoding="utf-8")

p = Path("tests/test_release_contract.py")
text = p.read_text(encoding="utf-8")
text = text.replace('assert version == "1.0.3"', 'assert version == "1.0.4"')
old_notes = '''    current_notes = Path("docs/RELEASE_NOTES_v1.0.3.md").read_text(encoding="utf-8")
    assert "interactive" in current_notes.lower()
    assert "--client-cert-file" in current_notes
    assert "v1.0.2" in current_notes
'''
new_notes = '''    v103_notes = Path("docs/RELEASE_NOTES_v1.0.3.md").read_text(encoding="utf-8")
    assert "interactive" in v103_notes.lower()
    assert "--client-cert-file" in v103_notes
    assert "v1.0.2" in v103_notes

    current_notes = Path("docs/RELEASE_NOTES_v1.0.4.md").read_text(encoding="utf-8")
    assert "admin" in current_notes.lower()
    assert "user" in current_notes.lower()
    assert "org.opencontainers.image.revision" in current_notes
'''
if old_notes not in text:
    raise SystemExit("v1.0.3 release-note contract block not found")
p.write_text(text.replace(old_notes, new_notes), encoding="utf-8")

# Repair the known v1.0.3 image-integrity gap for the new release only.
p = Path(".github/workflows/build.yml")
text = p.read_text(encoding="utf-8")
expr = lambda body: "$" + "{{ " + body + " }}"
tag_expr = expr("steps.image-tags.outputs.tags")
revision_expr = expr("github.sha")
repository_expr = expr("github.repository")
version_expr = expr("steps.release-version.outputs.version_tag || inputs.image_tag || github.ref_name")
old = "          push: true\n          tags: " + tag_expr + "\n"
new = (
    old
    + "          labels: |\n"
    + "            org.opencontainers.image.revision=" + revision_expr + "\n"
    + "            org.opencontainers.image.source=https://github.com/" + repository_expr + "\n"
    + "            org.opencontainers.image.version=" + version_expr + "\n"
)
if old not in text:
    raise SystemExit("docker build-push block not found")
p.write_text(text.replace(old, new), encoding="utf-8")

Path("docs/RELEASE_NOTES_v1.0.4.md").write_text(
    '''# Marzban v1.0.4

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
''',
    encoding="utf-8",
)
