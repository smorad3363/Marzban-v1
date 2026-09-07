const fs = require("fs");
const assert = require("assert");

const read = (p) => fs.readFileSync(p, "utf8");
const header = read("src/components/Header.tsx");
const shell = read("src/components/AppShell.tsx");
const dashboard = read("src/pages/Dashboard.tsx");
const bulk = read("src/components/BulkUserActions.tsx");
const scss = read("src/index.scss");
const chakra = read("chakra.config.ts");

assert(!header.includes("onResetAllUsage"), "reset-all usage trigger must be removed from configuration navigation");
assert(!header.includes("ResetUsageIcon"), "reset-all usage icon must be removed from configuration navigation");
assert(!header.includes("Operations workspace"), "default workspace subtitle must not render in sidebar");
assert(!header.includes("<BrandMark"), "default brand mark must not render in sidebar");
assert(header.includes('data-color-mode={colorMode}'), "sidebar must track active color mode explicitly");

for (const overlay of ["CoreSettingsModal", "HostsDialog", "NodesDialog", "NodesUsage"]) {
  assert(shell.includes(`<${overlay} />`), `${overlay} must be globally mounted in AppShell`);
}
assert(!dashboard.includes("ResetAllUsageModal"), "reset-all modal must not be mounted");
assert(!dashboard.includes("CoreSettingsModal"), "global overlays must not be duplicated in Dashboard");
assert(!dashboard.includes("وضعیت روشن، تصمیم بهتر، سرویس پایدارتر."), "dashboard slogan must be removed");
assert(!dashboard.includes("messageForToday"), "rotating dashboard slogan must be removed");

for (const label of ["وضعیت", "اعتبار", "پاک‌سازی"]) {
  assert(bulk.includes(label), `bulk toolbar must include compact ${label} group`);
}
for (let i = 0; i < 8; i += 1) {
  assert(bulk.includes(`actionDefinitions[${i}]`), `bulk operation ${i} must remain reachable`);
}
assert(bulk.includes("MenuButton") && bulk.includes("MenuList"), "bulk actions must use compact grouped menus");

assert(scss.includes('.operations-sidebar[data-color-mode="light"]'), "light sidebar palette override missing");
assert(scss.includes("background: #F1F5F9 !important"), "light sidebar background must be explicit");
assert(scss.includes(".chakra-modal__close-btn"), "modal close-button click-layer hardening missing");
assert(chakra.includes('pointerEvents: "auto"') && chakra.includes("zIndex: 30"), "modal close-button theme hardening missing");

console.log("v1.0.8 UI contract OK");
