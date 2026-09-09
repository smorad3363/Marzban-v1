const assert = require("node:assert/strict");
const fs = require("node:fs");
const path = require("node:path");

const root = path.resolve(__dirname, "..");
const read = (relativePath) => fs.readFileSync(path.join(root, relativePath), "utf8");

const router = read("src/pages/Router.tsx");
const dashboard = read("src/pages/Dashboard.tsx");
const usersPage = read("src/pages/Users.tsx");
const header = read("src/components/Header.tsx");
const plans = read("src/pages/Plans.tsx");
const deviceLimits = read("src/pages/DeviceLimits.tsx");
const appShell = read("src/components/AppShell.tsx");
const usersTable = read("src/components/UsersTablePro.tsx");
const adminForm = read("src/components/AdminFormDrawer.tsx");
const userDialog = read("src/components/UserDialog.tsx");
const createUserFromPlan = read("src/components/CreateUserFromPlan.tsx");
const adminsPage = read("src/pages/admins/AdminsPage.tsx");
const nodesWorkspace = read("src/components/NodesManagementWorkspace.tsx");

// Dashboard and Users must remain distinct surfaces.
assert.ok(router.includes('path: "/users/"'), "Users must have a dedicated route");
assert.ok(header.includes('to="/users/"'), "Navigation must expose the dedicated Users route");
assert.ok(dashboard.includes("مانده اعتبار"), "Admin dashboard must expose remaining credit");
assert.ok(dashboard.includes("اعتبار مالی"), "Admin dashboard must expose account credit");
assert.ok(!dashboard.includes("UserManagementControls"), "Dashboard must not embed user management controls");
assert.ok(usersPage.includes("UserManagementControls"), "Users page must own user management controls");
assert.ok(usersPage.includes("UsersTablePro"), "Users page must own the users table");
for (const hiddenCommercialLabel of ["بر اساس حجم مصرفی", "بر اساس حجم ساخته‌شده", "طبق پلن · سقف اکانت"]) {
  assert.ok(!dashboard.includes(hiddenCommercialLabel), `Admin self dashboard must hide commercial mode label: ${hiddenCommercialLabel}`);
}

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

// Delegated user creation contracts: Plans use the scoped endpoint; Form durations use Owner presets.
assert.ok(createUserFromPlan.includes('fetch("/available-user-plans")'), "Plan user creation must load only effective plans");
assert.ok(createUserFromPlan.includes('fetch("/users/from-plan"'), "Plan user creation must use the dedicated Plan endpoint");
assert.ok(createUserFromPlan.includes("access_group_id: Number(groupId)"), "Plan user creation must keep explicit Access Group selection");
assert.ok(userDialog.includes("allowed_form_duration_days"), "Form creation must consume Owner-approved duration presets");
assert.ok(userDialog.includes("restrictedDurationOptions"), "Restricted Form creation must render preset durations");
assert.ok(userDialog.includes("Math.floor(Date.now() / 1000) + selectedRestrictedDuration * 86400"), "Restricted Form expiry must be calculated from submit time");
assert.ok(userDialog.includes('display={restrictedCreate ? "none" : "block"}'), "Restricted Form creation must not expose the arbitrary calendar expiry control");

// Admin deletion is safe retirement: immutable history is retained while accounting state is not a blocker.
assert.ok(adminsPage.includes("حذف ادمین به‌صورت امن با بازنشسته‌سازی حساب انجام می‌شود"), "Admin deletion must explain safe retirement before submit");
assert.ok(adminsPage.includes("سابقه حسابداری و Audit حفظ می‌شود"), "Admin deletion must explain immutable history preservation");
assert.ok(adminsPage.includes("مانده اعتبار یا ترافیک مانع حذف نیست"), "Admin deletion must explain that accounting state does not block retirement");
assert.ok(adminsPage.includes("فقط ادمین دارای زیرمجموعه فعال"), "Admin deletion must keep the child-Admin blocker visible");

// Keep the already-correct global infrastructure modal architecture from regressing.
for (const modal of ["<CoreSettingsModal />", "<HostsDialog />", "<NodesDialog />"]) {
  assert.ok(appShell.includes(modal), `AppShell must keep ${modal} globally mounted`);
}
assert.ok(appShell.includes("{isOwner && ("), "global infrastructure modals must remain Owner-gated");

assert.ok(!appShell.includes("<NodesUsage />"), "Separate Nodes Usage modal must be removed after unified Node Operations is functional");
assert.ok(!header.includes("onShowingNodesUsage"), "Navigation must not expose the redundant Nodes Usage action");
assert.ok(nodesWorkspace.includes('fetch("/nodes/operations")'), "Unified Node Operations workspace must consume the operations summary endpoint");
assert.ok(nodesWorkspace.includes("/operations/history?minutes=1440&max_points=120"), "Unified Node Operations workspace must lazy-load bounded persisted history");
assert.ok(nodesWorkspace.includes("/events?offset=0&limit=50"), "Unified Node Operations workspace must lazy-load the sanitized event timeline");
assert.ok(nodesWorkspace.includes("میانگین ۱ ساعت") && nodesWorkspace.includes("میانگین ۲۴ ساعت"), "Unified Node Operations workspace must expose durable 1h/24h averages");
assert.ok(nodesWorkspace.includes("sortMode"), "Unified Node Operations workspace must expose deterministic sorting");

// Global API errors must expose a stable code, actionable Persian text and context.
const apiError = read("src/utils/apiError.ts");
const toastHandler = read("src/utils/toastHandler.ts");
const httpService = read("src/service/http.ts");
assert.ok(apiError.includes("candidate?.response?.data"), "API error parser must accept Axios-compatible response.data as well as ofetch data");
assert.ok(apiError.includes("[${info.code}] ${info.message}"), "Visible errors must include an error code and message");
assert.ok(apiError.includes("فیلد: ${field}"), "Visible errors must identify the failing field when available");
assert.ok(apiError.includes("کد پیگیری: ${info.requestId}"), "Visible errors must expose the request tracking id");
assert.ok(toastHandler.includes("localizedApiError(e, field)"), "Validation field errors must use the contextual formatter");
assert.ok(httpService.includes("error.message = localizedApiError(error)"), "All shared fetch failures must normalize legacy error.message");

console.log("stage 1 UI contracts: assertions passed");
