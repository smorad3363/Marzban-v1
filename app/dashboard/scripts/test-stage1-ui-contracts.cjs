const assert = require("node:assert/strict");
const fs = require("node:fs");
const path = require("node:path");

const root = path.resolve(__dirname, "..");
const read = (relativePath) => fs.readFileSync(path.join(root, relativePath), "utf8");

const router = read("src/pages/Router.tsx");
const header = read("src/components/Header.tsx");
const plans = read("src/pages/Plans.tsx");
const deviceLimits = read("src/pages/DeviceLimits.tsx");
const appShell = read("src/components/AppShell.tsx");
const usersTable = read("src/components/UsersTablePro.tsx");
const adminForm = read("src/components/AdminFormDrawer.tsx");

// Plans must use the same active-account + can_manage_plans contract across page, route and navigation.
assert.ok(router.includes("const PlanManagerOnly"), "Plans route must use a dedicated permission guard");
assert.ok(router.includes('account.data?.account_status === "ACTIVE"'), "Plans route must require an active delegated Admin account");
assert.ok(router.includes("account.data?.can_manage_plans"), "Plans route must honor can_manage_plans");
assert.ok(router.includes("<PlanManagerOnly><Plans /></PlanManagerOnly>"), "Plans route must be wrapped by PlanManagerOnly");
assert.ok(!router.includes("<OwnerOnly><Plans /></OwnerOnly>"), "Plans route must not regress to Owner-only access");

assert.ok(header.includes("const canAccessPlans = isOwner || Boolean("), "Plans navigation must derive delegated access explicitly");
assert.ok(header.includes('account.data?.account_status === "ACTIVE"'), "Plans navigation must hide access for inactive delegated Admins");
assert.ok(header.includes("account.data?.can_manage_plans"), "Plans navigation must honor can_manage_plans");
assert.equal((header.match(/hidden=\{!canAccessPlans\}/g) || []).length, 2, "mobile and desktop Plans navigation must use canAccessPlans");
assert.ok(!/hidden=\{!isOwner\}[\s\S]{0,220}to="\/plans\/"/.test(header), "Plans navigation must not regress to Owner-only visibility");

assert.ok(plans.includes('const accountActive = account.data?.account_status === "ACTIVE";'), "Plans page must require an active account");
assert.ok(plans.includes('account.data?.role === "OWNER" || account.data?.can_manage_plans'), "Plans page must match the delegated plan-management contract");

// Device Limits must inherit the shared Light/Dark panel theme instead of pinning old dark-only surfaces.
for (const hardCodedDark of ["#2b4437", "#14231b", "#243d31"]) {
  assert.ok(!deviceLimits.toLowerCase().includes(hardCodedDark), `Device Limits must not hard-code ${hardCodedDark}`);
}
assert.ok(!deviceLimits.includes("linear-gradient(145deg, rgba(14,25,20,.98), rgba(7,19,23,.98))"), "Device Limits runtime card must not force the old dark gradient");
assert.ok(deviceLimits.includes('bg="var(--panel-surface)"'), "Device Limits cards must use the shared panel surface token");
assert.ok(deviceLimits.includes('borderColor="var(--panel-border)"'), "Device Limits separators must use the shared panel border token");

// Users table must remain readable on mobile/tablet without removing columns or operations.
assert.ok(usersTable.includes('overflowX="auto"'), "Users table must allow controlled horizontal scrolling on narrow viewports");
assert.ok(usersTable.includes('minW="1500px"'), "Users table must keep a readable minimum width instead of squeezing every column");
assert.ok(usersTable.includes('whiteSpace: "nowrap"') && usersTable.includes('wordBreak: "keep-all"'), "Users table headers must not wrap character-by-character");
assert.ok(usersTable.includes("برای دیدن همه جزئیات و عملیات، جدول را به صورت افقی بکشید."), "Mobile/tablet users must get a horizontal-scroll affordance hint");
for (const action of ["کپی لینک اشتراک", "ویرایش", "حذف کاربر", "تمدید با پلن", "بازنشانی مصرف", "ابطال لینک اشتراک"]) {
  assert.ok(usersTable.includes(action), `Users table action must remain available: ${action}`);
}

// Admin creation must always expose the three supported billing contracts to the Owner.
for (const label of ["بر اساس حجم مصرفی", "بر اساس حجم ساخته‌شده", "طبق پلن · سقف اکانت"]) {
  assert.ok(adminForm.includes(label), `Admin billing mode must remain visible: ${label}`);
}
assert.ok(adminForm.includes("canonicalOwnerBillingModes"), "Owner billing mode fallback must remain explicit");
assert.ok(adminForm.includes('accountQuery.data?.role === "OWNER"'), "Owner fallback must be gated by the account role");
assert.ok(adminForm.includes("allowedModes.length === 0"), "Missing delegated billing modes must show a visible warning instead of a blank selector");

// Keep the already-correct global infrastructure modal architecture from regressing.
for (const modal of ["<CoreSettingsModal />", "<HostsDialog />", "<NodesDialog />", "<NodesUsage />"]) {
  assert.ok(appShell.includes(modal), `AppShell must keep ${modal} globally mounted`);
}
assert.ok(appShell.includes("{isOwner && ("), "global infrastructure modals must remain Owner-gated");

console.log("stage 1 UI contracts: assertions passed");
