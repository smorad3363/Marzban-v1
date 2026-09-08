const assert = require("node:assert/strict");
const fs = require("node:fs");
const path = require("node:path");
const root = path.resolve(__dirname, "..");
const read = (p) => fs.readFileSync(path.join(root, p), "utf8");

const styles = read("src/index.scss");
const theme = read("chakra.config.ts");
const header = read("src/components/Header.tsx");
const branding = read("src/components/BrandingControls.tsx");
const filters = read("src/components/FiltersCompact.tsx");
const users = read("src/components/UsersTablePro.tsx");
const bulk = read("src/components/BulkUserActions.tsx");
const device = read("src/components/UserDeviceLimit.tsx");
const dashboard = read("src/pages/Dashboard.tsx");
const nodesModal = read("src/components/NodesModal.tsx");
const nodesWorkspace = read("src/components/NodesManagementWorkspace.tsx");
const groups = read("src/components/AccessGroupManager.tsx");
const plans = read("src/pages/Plans.tsx");
const settings = read("src/pages/Settings.tsx");
const adminTable = read("src/pages/admins/AdminTable.tsx");

for (const hex of [
  "#F8FAFC", "#FFFFFF", "#F1F5F9", "#E2E8F0", "#0F172A", "#334155", "#64748B", "#2563EB", "#1D4ED8", "#16A34A", "#D97706", "#DC2626", "#0891B2",
  "#0B0F19", "#131826", "#0F1420", "#1F2937", "#F1F5F9", "#CBD5E1", "#7C8AA0", "#3B82F6", "#60A5FA", "#22C55E", "#F59E0B", "#EF4444", "#22D3EE",
]) assert.ok(styles.includes(hex), `missing approved palette value ${hex}`);
assert.ok(!styles.includes('data-panel-theme="black_gold"'));
assert.ok(!branding.includes("black_gold") && !branding.includes("heisenberg") && !branding.includes("طلایی"));
assert.ok(header.includes("toggleColorMode") && header.includes("تم روشن") && header.includes("تم تیره"));
assert.ok(theme.includes('borderRadius: "12px"') && theme.includes('borderRadius: "16px"'));
assert.ok(theme.includes('borderBottom: "0"') && theme.includes("--panel-row-alt"));

assert.ok(!dashboard.includes("NodeBandwidthPanel"), "Node bandwidth panel must be removed from the main Dashboard");
assert.ok(dashboard.includes("UserManagementControls"), "combined user management controls must be on Dashboard");
assert.ok(nodesModal.includes("NodesManagementWorkspace"), "Node settings must use the reviewed management workspace");
for (const marker of ["نگهبان نودها", "nodes-live-bandwidth", "Sparkline", "افزودن نود"]) assert.ok(nodesWorkspace.includes(marker), `Node workspace marker missing: ${marker}`);

assert.ok(filters.includes("sortOptions") && filters.includes("SortButton"), "sorts must be direct buttons");
assert.ok(filters.includes("همه ادمین‌ها") && filters.includes('aria-label="فیلتر ادمین"'), "Admin must remain the dropdown filter");
assert.ok(!filters.includes("AdvancedIcon"), "old advanced-filter dropdown must not return");
for (const status of ["همه کاربران", "فعال", "غیرفعال", "منقضی", "در انتظار"]) assert.ok(filters.includes(status));

assert.ok(bulk.includes("users.length > 0"), "selected-user bulk controls must stay hidden without a selection");
for (const key of ["bulkActivate", "bulkDeactivate", "bulkAddVolume", "bulkSubtractVolume", "bulkAddDays", "bulkSubtractDays", "bulkAddVolumeAndDays", "bulkDeleteSelected"]) assert.ok(bulk.includes(key), `bulk action missing: ${key}`);
assert.ok(!bulk.includes("Retry خطاهای") && !bulk.includes("گزارش job") && !bulk.includes("هدف snapshot"), "mixed UI copy must be normalized");

assert.ok(users.includes("<Progress") && users.includes('h="4px"'), "thin traffic progress bar must be preserved");
assert.ok(users.includes('boxSize="6px"') && users.includes('borderColor={meta.border}'), "soft status badge + dot must be preserved");
assert.ok(users.includes("<MenuButton") && users.includes("عملیات بیشتر"), "secondary row actions stay in kebab menu");
assert.ok(users.includes("<UserDeviceLimit user={user} compact"), "Device Limit shield must be restored in user rows");
assert.ok(device.includes("compact?: boolean") && device.includes('minW={compact ? "30px" : "44px"}'));
assert.ok(users.indexOf("<BulkUserActions") < users.indexOf("<TableContainer"), "bulk toolbar must stay outside the horizontal scroll region");
assert.ok(users.includes('overflowX="auto"'), "users table must expose controlled horizontal scrolling on narrow viewports");
assert.ok(users.includes('minW="1500px"'), "users table must keep a readable minimum width instead of squeezing all columns");
assert.ok(users.includes('whiteSpace: "nowrap"') && users.includes('wordBreak: "keep-all"'), "users table headers must not wrap character-by-character");
assert.ok(users.includes("برای دیدن همه جزئیات و عملیات، جدول را به صورت افقی بکشید."), "narrow viewports must explain the horizontal-scroll affordance");
assert.ok(users.includes('data-disabled={user.status === "disabled"'));

assert.ok(plans.includes('id="access-groups"') && plans.includes("گروه‌های دسترسی"));
assert.ok(plans.includes("<AccessGroupManager />") && !settings.includes("<AccessGroupManager />"));
for (const oldCopy of ["Access Group جدید", "Nodeها", "Inbound و Hostهای مجاز", "هنوز Access Group ساخته نشده"]) assert.ok(!groups.includes(oldCopy), `mixed Access Group copy remains: ${oldCopy}`);
assert.ok(header.includes(">پیکربندی</Button>"));
assert.ok(adminTable.includes("<StatusPill") && adminTable.includes("عملیات سریع"), "modular Admin UI must remain intact");

console.log("v1.0.7 UI/UX contract: assertions passed");
