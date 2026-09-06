from pathlib import Path


def replace(path: str, old: str, new: str, count: int = -1) -> None:
    p = Path(path)
    text = p.read_text()
    if old not in text:
        return
    p.write_text(text.replace(old, new, count))


def main() -> None:
    dashboard = Path("app/dashboard/src/pages/Dashboard.tsx")
    d = dashboard.read_text()
    if 'import { NodeBandwidthPanel } from "components/NodeBandwidthPanel";' not in d:
        d = d.replace(
            'import { NodesDialog } from "components/NodesModal";\n',
            'import { NodesDialog } from "components/NodesModal";\nimport { NodeBandwidthPanel } from "components/NodeBandwidthPanel";\n',
        )
    d = d.replace(
        '              <Text mt={1} color="gray.400" fontSize="12px">مرکز مدیریت کاربران و سرویس‌های Marzban</Text>\n',
        '',
    )
    if '{isOwner && <NodeBandwidthPanel />}' not in d:
        d = d.replace(
            '        <DashboardOverviewCompact />\n',
            '        <DashboardOverviewCompact />\n        {isOwner && <NodeBandwidthPanel />}\n',
        )
    d = d.replace(
        'color="blue.300" fontSize="11px" fontWeight="800"',
        'color="var(--panel-accent)" fontSize="11px" fontWeight="800"',
    )
    d = d.replace('borderColor="rgba(148,163,184,.14)"', 'borderColor="var(--panel-border)"')
    d = d.replace('boxShadow="0 16px 42px rgba(0,0,0,.22)"', 'boxShadow="var(--shadow-panel)"')
    dashboard.write_text(d)

    overview = Path("app/dashboard/src/components/DashboardOverviewCompact.tsx")
    o = overview.read_text()
    for old, new in {
        'tone = "gray.100"': 'tone = "var(--panel-text)"',
        'color="gray.400" fontSize="11px"': 'color="var(--panel-text-muted)" fontSize="11px"',
        'color="gray.500" fontSize="10px"': 'color="var(--panel-text-muted)" fontSize="10px"',
        'color="primary.300"': 'color="var(--panel-accent)"',
        'tone={system.isError ? "orange.300" : "green.300"}': 'tone={system.isError ? "var(--panel-warning)" : "var(--panel-success)"}',
        'tone="green.300"': 'tone="var(--panel-success)"',
        'tone="blue.200"': 'tone="var(--panel-accent)"',
        'color="gray.400">CPU': 'color="var(--panel-text-muted)">CPU',
        'color="gray.400">حافظه': 'color="var(--panel-text-muted)">حافظه',
        '<DownIcon color="#60a5fa" />': '<DownIcon color="var(--panel-accent)" />',
        '<UpIcon color="#a78bfa" />': '<UpIcon color="var(--panel-accent)" />',
    }.items():
        o = o.replace(old, new)
    overview.write_text(o)

    node_panel = Path("app/dashboard/src/components/NodeBandwidthPanel.tsx")
    n = node_panel.read_text()
    n = n.replace(
        'if (state === "warming_up") return { label: "در حال نمونه‌گیری", scheme: "blue" };',
        'if (state === "warming_up") return { label: "در حال نمونه‌گیری", scheme: "primary" };',
    )
    n = n.replace('color="gray.500" _dark={{ color: "gray.400" }}', 'color="var(--panel-text-muted)"')
    n = n.replace('color="primary.600" _dark={{ color: "primary.300" }}', 'color="var(--panel-accent)"')
    n = n.replace('color="gray.600" _dark={{ color: "gray.400" }}', 'color="var(--panel-text-muted)"')
    n = n.replace('color="gray.500"', 'color="var(--panel-text-muted)"')
    node_panel.write_text(n)

    filters = Path("app/dashboard/src/components/FiltersCompact.tsx")
    f = filters.read_text()
    f = f.replace(
        '  bg: "rgba(2,6,23,.48)",\n  color: "gray.100",\n  borderColor: "rgba(148,163,184,.18)",\n  _hover: { borderColor: "rgba(148,163,184,.34)" },\n  _focusVisible: { borderColor: "yellow.400", boxShadow: "0 0 0 2px rgba(250,204,21,.12)" },',
        '  bg: "var(--panel-nested)",\n  color: "var(--panel-text)",\n  borderColor: "var(--panel-border)",\n  _hover: { borderColor: "var(--panel-border-strong)" },\n  _focusVisible: { borderColor: "var(--panel-accent)", boxShadow: "0 0 0 2px var(--panel-accent-soft)" },',
    )
    f = f.replace('tone?: "green" | "red" | "blue" | "yellow";', 'tone?: "primary" | "green" | "red" | "orange" | "gray";')
    f = f.replace('}> = ({ active, label, onClick, tone = "yellow" }) => (', '}> = ({ active, label, onClick, tone = "primary" }) => (')
    f = f.replace('colorScheme="yellow"\n              color="gray.900"', 'colorScheme="primary"\n              color="var(--panel-accent-contrast)"')
    f = f.replace('tone="blue" onClick={() => setStatus("disabled")}', 'tone="gray" onClick={() => setStatus("disabled")}')
    f = f.replace('tone="yellow" onClick={() => setStatus("on_hold")}', 'tone="orange" onClick={() => setStatus("on_hold")}')
    f = f.replace('borderColor="rgba(148,163,184,.18)"', 'borderColor="var(--panel-border)"')
    f = f.replace('borderColor="rgba(148,163,184,.10)"', 'borderColor="var(--panel-border)"')
    f = f.replace('sx={{ option: { background: "#080f19", color: "#f8fafc" } }}', 'sx={{ option: { background: "var(--panel-surface)", color: "var(--panel-text)" } }}')
    filters.write_text(f)

    bulk = Path("app/dashboard/src/components/BulkUserActions.tsx")
    b = bulk.read_text()
    b = b.replace('bg="rgba(15, 23, 42, .62)"', 'bg="var(--panel-nested)"')
    b = b.replace(
        'users.length > 0 ? "rgba(45, 212, 191, .3)" : "whiteAlpha.100"',
        'users.length > 0 ? "var(--panel-accent-border)" : "var(--panel-border)"',
    )
    b = b.replace('colorScheme="teal"', 'colorScheme="primary"')
    b = b.replace(
        'bg={users.length > 0 ? "rgba(45, 212, 191, .12)" : "whiteAlpha.50"}',
        'bg={users.length > 0 ? "var(--panel-accent-soft)" : "var(--panel-surface)"}',
    )
    b = b.replace(
        'color={users.length > 0 ? "teal.200" : "gray.400"}',
        'color={users.length > 0 ? "var(--panel-accent)" : "var(--panel-text-muted)"}',
    )
    b = b.replace(
        'bg="#111827"\n                borderColor="whiteAlpha.200"',
        'bg="var(--panel-surface)"\n                borderColor="var(--panel-border)"',
    )
    bulk.write_text(b)

    users = Path("app/dashboard/src/components/UsersTablePro.tsx")
    u = users.read_text()
    u = u.replace(
        'connecting: { label: "در اتصال", color: "cyan.200", bg: "rgba(6,182,212,.12)" },',
        'connecting: { label: "در اتصال", color: "var(--panel-accent)", bg: "var(--panel-accent-soft)" },',
    )
    u = u.replace(
        'const color = percent >= 90 ? "#ef4444" : percent >= 70 ? "#eab308" : "#22c55e";',
        'const color = percent >= 90 ? "var(--panel-danger)" : percent >= 70 ? "var(--panel-warning)" : "var(--panel-success)";',
    )
    u = u.replace('color={unlimited ? "#3b82f6" : color}', 'color={unlimited ? "var(--panel-accent)" : color}')
    u = u.replace(
        'gray: { color: "gray.200", bg: "rgba(148,163,184,.07)", border: "rgba(148,163,184,.18)" },',
        'gray: { color: "var(--panel-text-muted)", bg: "var(--panel-muted-soft)", border: "var(--panel-border)" },',
    )
    u = u.replace(
        'blue: { color: "blue.200", bg: "rgba(59,130,246,.12)", border: "rgba(96,165,250,.22)" },',
        'blue: { color: "var(--panel-accent)", bg: "var(--panel-accent-soft)", border: "var(--panel-accent-border)" },',
    )
    u = u.replace(
        'green: { color: "green.200", bg: "rgba(34,197,94,.11)", border: "rgba(74,222,128,.20)" },',
        'green: { color: "var(--panel-success)", bg: "var(--panel-success-soft)", border: "var(--panel-success-border)" },',
    )
    u = u.replace(
        'yellow: { color: "yellow.200", bg: "rgba(234,179,8,.11)", border: "rgba(250,204,21,.20)" },',
        'yellow: { color: "var(--panel-warning)", bg: "var(--panel-warning-soft)", border: "var(--panel-warning-border)" },',
    )
    u = u.replace(
        'red: { color: "red.200", bg: "rgba(239,68,68,.11)", border: "rgba(248,113,113,.20)" },',
        'red: { color: "var(--panel-danger)", bg: "var(--panel-danger-soft)", border: "var(--panel-danger-border)" },',
    )
    u = u.replace('colorScheme="yellow"', 'colorScheme="primary"')
    u = u.replace('color="yellow.300"', 'color="var(--panel-warning)"')
    u = u.replace('bg="rgba(2,8,23,.46)"', 'bg="var(--panel-nested)"')
    u = u.replace('borderColor="rgba(148,163,184,.12)"', 'borderColor="var(--panel-border)"')
    u = u.replace('borderColor: "rgba(148,163,184,.10)"', 'borderColor: "var(--panel-border)"')
    u = u.replace(
        'bg={selectedMap.has(user.username) ? "rgba(234,179,8,.045)" : "transparent"}',
        'bg={selectedMap.has(user.username) ? "var(--panel-accent-soft)" : "transparent"}',
    )
    u = u.replace(
        '_hover={{ bg: selectedMap.has(user.username) ? "rgba(234,179,8,.07)" : "rgba(255,255,255,.025)" }}',
        '_hover={{ bg: selectedMap.has(user.username) ? "var(--panel-accent-soft-strong)" : "var(--panel-row-hover)" }}',
    )
    u = u.replace(
        'bg="rgba(59,130,246,.18)" color="blue.100"',
        'bg="var(--panel-accent-soft)" color="var(--panel-accent)"',
    )
    u = u.replace('color="cyan.200"', 'color="var(--panel-accent)"')
    u = u.replace('colorScheme="yellow" variant="outline"', 'colorScheme="primary" variant="outline"')
    u = u.replace(
        'onClick={() => { renewalRequest.current = null; setRenewalUser(user); setRenewalPlanId(""); renewalModal.onOpen(); }} tone="yellow"',
        'onClick={() => { renewalRequest.current = null; setRenewalUser(user); setRenewalPlanId(""); renewalModal.onOpen(); }} tone="blue"',
    )
    users.write_text(u)

    header = Path("app/dashboard/src/components/Header.tsx")
    h = header.read_text()
    h = h.replace('bg="rgba(11, 16, 32, .98)"', 'bg="var(--panel-sidebar)"')
    h = h.replace('filter="drop-shadow(0 8px 20px var(--panel-glow))"', 'filter="none"')
    h = h.replace('colorScheme={isAuditPage ? "cyan" : "gray"}', 'colorScheme={isAuditPage ? "primary" : "gray"}')
    h = h.replace('color={isAuditPage ? "#06161a" : "gray.200"}', 'color={isAuditPage ? "var(--panel-accent-contrast)" : "gray.200"}')
    for old in ("#07130e", "#08111f"):
        h = h.replace(f'color={{isUsersPage ? "{old}" : "gray.200"}}', 'color={isUsersPage ? "var(--panel-accent-contrast)" : "gray.200"}')
        h = h.replace(f'color={{isPlansPage ? "{old}" : "gray.200"}}', 'color={isPlansPage ? "var(--panel-accent-contrast)" : "gray.200"}')
        h = h.replace(f'color={{isAdminsPage ? "{old}" : "gray.200"}}', 'color={isAdminsPage ? "var(--panel-accent-contrast)" : "gray.200"}')
        h = h.replace(f'color={{isDeviceLimitPage ? "{old}" : "gray.200"}}', 'color={isDeviceLimitPage ? "var(--panel-accent-contrast)" : "gray.200"}')
    h = h.replace('color={isSettingsPage ? "white" : "gray.200"}', 'color={isSettingsPage ? "var(--panel-accent-contrast)" : "gray.200"}')
    header.write_text(h)

    styles = Path("app/dashboard/src/index.scss")
    s = styles.read_text()
    marker = "/* dashboard palette normalization */"
    if marker not in s:
        s += r'''

/* dashboard palette normalization */
:root {
  --panel-bg: #f5f7fa;
  --panel-surface: #ffffff;
  --panel-nested: #eef2f6;
  --panel-border: #d7e0ea;
  --panel-border-strong: #b7c4d3;
  --panel-text: #111827;
  --panel-text-muted: #64748b;
  --panel-accent: #2563eb;
  --panel-accent-soft: rgba(37, 99, 235, .09);
  --panel-accent-soft-strong: rgba(37, 99, 235, .14);
  --panel-accent-border: rgba(37, 99, 235, .28);
  --panel-accent-contrast: #ffffff;
  --panel-sidebar: #0f172a;
  --panel-success: #15803d;
  --panel-success-soft: rgba(21, 128, 61, .10);
  --panel-success-border: rgba(21, 128, 61, .25);
  --panel-warning: #b45309;
  --panel-warning-soft: rgba(180, 83, 9, .10);
  --panel-warning-border: rgba(180, 83, 9, .25);
  --panel-danger: #dc2626;
  --panel-danger-soft: rgba(220, 38, 38, .09);
  --panel-danger-border: rgba(220, 38, 38, .24);
  --panel-muted-soft: rgba(100, 116, 139, .08);
  --panel-row-hover: rgba(15, 23, 42, .035);
  --panel-glow: transparent;
  --shadow-panel: 0 1px 2px rgba(15, 23, 42, .05), 0 10px 28px rgba(15, 23, 42, .07);
}

.chakra-ui-dark {
  --panel-bg: #0b1220;
  --panel-surface: #111a2b;
  --panel-nested: #162235;
  --panel-border: #2a3a52;
  --panel-border-strong: #40536f;
  --panel-text: #e8eef7;
  --panel-text-muted: #94a3b8;
  --panel-accent: #60a5fa;
  --panel-accent-soft: rgba(96, 165, 250, .10);
  --panel-accent-soft-strong: rgba(96, 165, 250, .16);
  --panel-accent-border: rgba(96, 165, 250, .30);
  --panel-accent-contrast: #07111f;
  --panel-sidebar: #09111f;
  --panel-success: #67c587;
  --panel-success-soft: rgba(103, 197, 135, .10);
  --panel-success-border: rgba(103, 197, 135, .25);
  --panel-warning: #e0a458;
  --panel-warning-soft: rgba(224, 164, 88, .10);
  --panel-warning-border: rgba(224, 164, 88, .25);
  --panel-danger: #ef8580;
  --panel-danger-soft: rgba(239, 133, 128, .10);
  --panel-danger-border: rgba(239, 133, 128, .25);
  --panel-muted-soft: rgba(148, 163, 184, .07);
  --panel-row-hover: rgba(255, 255, 255, .025);
  --shadow-panel: 0 1px 2px rgba(0, 0, 0, .22), 0 12px 30px rgba(0, 0, 0, .18);
}

html[data-panel-theme="black_gold"] {
  --panel-bg: #090a0a;
  --panel-surface: #101112;
  --panel-nested: #171817;
  --panel-border: #3e3829;
  --panel-border-strong: #665a38;
  --panel-text: #eee9dc;
  --panel-text-muted: #a8a08e;
  --panel-accent: #d3ab4c;
  --panel-accent-soft: rgba(211, 171, 76, .10);
  --panel-accent-soft-strong: rgba(211, 171, 76, .16);
  --panel-accent-border: rgba(211, 171, 76, .30);
  --panel-accent-contrast: #171204;
  --panel-sidebar: #090a0a;
  --panel-success: #76b48a;
  --panel-success-soft: rgba(118, 180, 138, .10);
  --panel-success-border: rgba(118, 180, 138, .24);
  --panel-warning: #d3ab4c;
  --panel-warning-soft: rgba(211, 171, 76, .10);
  --panel-warning-border: rgba(211, 171, 76, .28);
  --panel-danger: #df817b;
  --panel-danger-soft: rgba(223, 129, 123, .10);
  --panel-danger-border: rgba(223, 129, 123, .25);
  --panel-muted-soft: rgba(168, 160, 142, .07);
  --panel-row-hover: rgba(211, 171, 76, .035);
  --panel-glow: transparent;
}

body {
  color: var(--panel-text) !important;
  background-color: var(--panel-bg) !important;
  background-image: none !important;
}

.operations-shell::before,
.operations-grid {
  background-image: none !important;
}

html[data-panel-theme="black_gold"] body,
html[data-panel-theme="black_gold"] .chakra-card,
html[data-panel-theme="black_gold"] .chakra-modal__content,
html[data-panel-theme="black_gold"] .chakra-drawer__content {
  color: var(--panel-text) !important;
}

html[data-panel-theme="black_gold"] aside {
  background: var(--panel-sidebar) !important;
}

html[data-panel-theme="black_gold"] .chakra-table td {
  color: var(--panel-text);
}

html[data-panel-theme="black_gold"] .chakra-table th {
  color: var(--panel-text-muted);
}
'''
    styles.write_text(s)

    test = Path("app/dashboard/scripts/test-admin-ux.cjs")
    t = test.read_text()
    if 'const compactOverview = read("src/components/DashboardOverviewCompact.tsx");' not in t:
        t = t.replace(
            'const dashboard = read("src/pages/Dashboard.tsx");\n',
            'const dashboard = read("src/pages/Dashboard.tsx");\nconst compactOverview = read("src/components/DashboardOverviewCompact.tsx");\nconst nodeBandwidthPanel = read("src/components/NodeBandwidthPanel.tsx");\nconst dashboardStyles = read("src/index.scss");\n',
        )
    additions = '''assert.ok(!dashboard.includes("مرکز مدیریت کاربران و سرویس‌های Marzban"), "dashboard welcome header must not include the redundant Marzban management subtitle");
assert.ok(dashboard.includes("{isOwner && <NodeBandwidthPanel />}"), "Owner dashboard must render the real node bandwidth panel");
assert.ok(nodeBandwidthPanel.includes('fetch("/nodes/bandwidth")'), "node bandwidth panel must use the real bounded node bandwidth endpoint");
assert.ok(compactOverview.includes("var(--panel-accent)") && !compactOverview.includes('tone="blue.200"'), "compact dashboard accents must follow the selected panel palette");
assert.ok(dashboardStyles.includes("dashboard palette normalization") && dashboardStyles.includes("--panel-accent-soft") && dashboardStyles.includes('html[data-panel-theme="black_gold"]'), "dashboard palette tokens must define coherent blue and black-gold themes");
'''
    if additions not in t:
        anchor = 'assert.ok(dashboard.includes("<AdminFormDrawer") && dashboard.includes("<PlanCreateModal"), "Dashboard quick-create forms must open in place");\n'
        if anchor not in t:
            raise SystemExit("test contract anchor not found")
        t = t.replace(anchor, anchor + additions)
    test.write_text(t)


if __name__ == "__main__":
    main()
