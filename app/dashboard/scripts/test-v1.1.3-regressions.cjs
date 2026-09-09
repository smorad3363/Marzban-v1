const fs = require("fs");
const assert = require("assert");
const nodePath = require("path");
const read = (file) => fs.readFileSync(
  file.startsWith("../../")
    ? nodePath.resolve(__dirname, file)
    : nodePath.resolve(__dirname, "..", file),
  "utf8"
);
const adminForm = read("src/components/AdminFormDrawer.tsx");
const plans = read("src/pages/Plans.tsx");
const backendAdmin = read("../../routers/admin.py");
const accessGroups = read("../../utils/access_groups.py");
const crud = read("../../db/crud.py");
assert(adminForm.includes("plan_category_ids: admin.plan_category_ids ?? []"));
assert(adminForm.includes('fetch("/plan-categories")'));
assert(adminForm.includes("حداقل یک دسته‌بندی پلن"));
assert(plans.includes("allowed_admin_ids: editing ? editing.allowed_admin_ids : []"));
assert((backendAdmin.match(/replace_admin_categories\(/g) || []).length >= 2);
assert(!accessGroups.includes("access_group_permission_in_use"));
assert(accessGroups.includes("_validated_network_scope(db, user.access_group_id)"));
assert(crud.includes("Admin.deleted_at.is_(None)"));
assert(crud.includes("dbadmin.deleted_at = datetime.utcnow()"));
console.log("v1.1.3 regressions: assertions passed");
