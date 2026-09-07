from pathlib import Path

path = Path('app/dashboard/scripts/test-admin-ux.cjs')
text = path.read_text(encoding='utf-8')
old_read = 'const dashboard = read("src/pages/Dashboard.tsx");\n'
new_read = old_read + 'const appShell = read("src/components/AppShell.tsx");\n'
if 'const appShell = read("src/components/AppShell.tsx");' not in text:
    if old_read not in text:
        raise SystemExit('admin UX dashboard read marker missing')
    text = text.replace(old_read, new_read, 1)
old_assert = 'assert.ok(dashboard.includes("{isOwner && ("), "Owner-only infrastructure dialogs must not query restricted APIs for children");'
new_assert = 'assert.ok(appShell.includes("{isOwner && (") && appShell.includes("<CoreSettingsModal />") && appShell.includes("<HostsDialog />") && appShell.includes("<NodesDialog />") && appShell.includes("<NodesUsage />"), "Owner-only infrastructure dialogs must be globally mounted without querying restricted APIs for children");'
if old_assert not in text and new_assert not in text:
    raise SystemExit('admin UX owner-only assertion marker missing')
text = text.replace(old_assert, new_assert, 1)
path.write_text(text, encoding='utf-8')
print('v1.0.8 admin UX contract updated')
