const fs = require("fs");
const path = require("path");
const assert = require("assert");

const root = path.resolve(__dirname, "..");
const read = (relativePath) => fs.readFileSync(path.join(root, relativePath), "utf8");

const appShell = read("src/components/AppShell.tsx");
const adminForm = read("src/components/AdminFormDrawer.tsx");
const createUserFromPlan = read("src/components/CreateUserFromPlanModal.tsx");
const userDialog = read("src/components/UserDialog.tsx");
const adminsPage = read("src/pages/admins/AdminsPage.tsx");
const usersTable = read("src/pages/users/UsersTable.tsx");

// Keep the dense user table readable and preserve every row action.
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

// Admin deletion is safe retirement: immutable history is retained while balances/history do not block retirement.
assert.ok(adminsPage.includes("حذف ادمین به‌صورت امن با بازنشسته‌سازی حساب انجام می‌شود"), "Admin deletion must explain safe retirement before submit");
assert.ok(adminsPage.includes("سابقه حسابداری و Audit حفظ می‌شود"), "Admin deletion must explain that immutable history is preserved");
assert.ok(adminsPage.includes("مانده اعتبار یا ترافیک مانع حذف نیست"), "Admin deletion must not imply accounting balances block retirement");
assert.ok(adminsPage.includes("فقط ادمین دارای زیرمجموعه فعال"), "Admin deletion must keep the active-child structural blocker visible");

// Keep the already-correct global infrastructure modal architecture from regressing.
for (const modal of ["<CoreSettingsModal />", "<HostsDialog />", "<NodesDialog />", "<NodesUsage />"]) {
  assert.ok(appShell.includes(modal), `AppShell must keep ${modal} globally mounted`);
}
assert.ok(appShell.includes("{isOwner && ("), "global infrastructure modals must remain Owner-gated");

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
