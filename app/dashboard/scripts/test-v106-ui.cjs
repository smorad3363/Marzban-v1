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
const plans = read("src/pages/Plans.tsx");
const settings = read("src/pages/Settings.tsx");
const adminTable = read("src/pages/admins/AdminTable.tsx");

for (const hex of [
  "#F8FAFC", "#FFFFFF", "#F1F5F9", "#E2E8F0", "#0F172A", "#334155", "#64748B", "#2563EB", "#1D4ED8", "#16A34A", "#D97706", "#DC2626", "#0891B2",
  "#0B0F19", "#131826", "#0F1420", "#1F2937", "#F1F5F9", "#CBD5E1", "#7C8AA0", "#3B82F6", "#60A5FA", "#22C55E", "#F59E0B", "#EF4444", "#22D3EE",
]) assert.ok(styles.includes(hex), `missing approved palette value ${hex}`);

assert.ok(!styles.includes('data-panel-theme="black_gold"'), "black-gold theme must not remain active in CSS");
assert.ok(!branding.includes("black_gold") && !branding.includes("heisenberg") && !branding.includes("طلایی"), "branding controls must not expose a second theme axis");
assert.ok(header.includes("toggleColorMode") && header.includes("تم روشن") && header.includes("تم تیره"), "header must expose exactly the light/dark color-mode toggle");
assert.ok(theme.includes('borderRadius: "12px"') && theme.includes('borderRadius: "16px"'), "controls and cards must use the unified 12/16px radius system");
assert.ok(theme.includes('borderBottom: "0"') && theme.includes("--panel-row-alt"), "tables must avoid row borders and use subtle zebra rows");

assert.ok(users.includes("<Progress") && users.includes('h="4px"'), "traffic usage must use a thin progress bar");
assert.ok(users.includes('boxSize="6px"') && users.includes('borderColor={meta.border}'), "user status must be a soft outline badge with a status dot");
for (const action of ["کپی لینک اشتراک", "ویرایش", "حذف کاربر", "QR Code", "گزارش فعالیت", "تمدید با پلن", "بازنشانی مصرف", "ابطال لینک اشتراک"]) {
  assert.ok(users.includes(action), `user action lost during UX cleanup: ${action}`);
}
assert.ok(users.includes("<MenuButton") && users.includes("عملیات بیشتر"), "secondary user actions must live in the kebab menu");
assert.ok(users.includes('data-disabled={user.status === "disabled"'), "disabled user rows must have a dedicated subdued state");

for (const status of ["همه", "فعال", "غیرفعال", "منقضی", "در انتظار"]) assert.ok(filters.includes(status), `status filter missing: ${status}`);
assert.ok(filters.includes("StatusSegment") && filters.includes("AdvancedIcon") && filters.includes("<Collapse"), "toolbar must use segmented statuses plus collapsible advanced filters");
assert.ok(filters.includes("همه ادمین‌ها") && filters.includes("مرتب‌سازی کاربران"), "advanced filtering options must be preserved");

assert.ok(plans.includes("<AccessGroupManager />"), "Access Group management must live with Plans");
assert.ok(!settings.includes("<AccessGroupManager />"), "Access Group management must be removed from Configuration/Settings");
assert.ok(header.includes(">پیکربندی</Button>"), "navigation must present Settings as Configuration");
assert.ok(adminTable.includes("<StatusPill") && adminTable.includes("عملیات سریع"), "current modular Admin UI must remain intact");

console.log("v1.0.6 UI/UX contract: assertions passed");
