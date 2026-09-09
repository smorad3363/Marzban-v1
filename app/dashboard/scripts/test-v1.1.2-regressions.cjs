const assert = require("node:assert/strict");
const fs = require("node:fs");
const path = require("node:path");

const root = path.resolve(__dirname, "..");
const read = (relativePath) => fs.readFileSync(path.join(root, relativePath), "utf8");

const drawer = read("src/components/AdminFormDrawer.tsx");
const router = read("src/pages/Router.tsx");
const header = read("src/components/Header.tsx");
const filters = read("src/components/FiltersCompact.tsx");
const planCreate = read("src/components/CreateUserFromPlan.tsx");
const adminsPage = read("src/pages/admins/AdminsPage.tsx");

assert.ok(
  !drawer.includes('mode === "USER_CREDIT" && <FormHelperText>'),
  "USER_CREDIT helper text must not depend on FormControl context"
);
assert.ok(
  drawer.includes('mode === "USER_CREDIT" && <Text') && drawer.includes("سقف اکانت"),
  "USER_CREDIT must keep its Plan-only explanatory hint"
);
assert.ok(
  router.includes("Unable to render this page") && router.includes("Unable to reach the service"),
  "route error UI must distinguish client render failures from service failures"
);
assert.ok(
  header.includes("queryClient.clear()") && header.includes('navigate("/login/", { replace: true })'),
  "logout must clear auth-scoped query cache and replace browser history"
);
assert.ok(
  filters.includes('["FREE_FORM", "FORM_ONLY", "BOTH"]') &&
  filters.includes('["PLAN_ONLY", "BOTH"]') &&
  filters.includes('billing_mode === "USER_CREDIT"'),
  "dashboard creation actions must preserve Form-only, Plan-only, Both and USER_CREDIT behavior"
);
assert.ok(
  planCreate.includes('fetch("/available-user-plans")'),
  "Plan creation must use the scoped available-user-plans endpoint"
);
assert.ok(
  adminsPage.includes('fetch(`/admin/${username}`, { method: "DELETE", body: { strategy } })'),
  "Admin deletion must keep sending the selected cleanup strategy"
);

console.log("v1.1.2 dashboard regression checks passed");
