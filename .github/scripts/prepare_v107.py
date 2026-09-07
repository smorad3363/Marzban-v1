from pathlib import Path
import re
import subprocess

ROOT = Path(__file__).resolve().parents[2]

def run(*args):
    subprocess.run(args, cwd=ROOT, check=True)

def read(path):
    return (ROOT / path).read_text()

def write(path, text):
    (ROOT / path).write_text(text)

def must_replace(text, old, new, label, count=None):
    actual = text.count(old)
    if actual == 0:
        raise RuntimeError(f"missing replacement target: {label}")
    if count is not None and actual != count:
        raise RuntimeError(f"unexpected replacement count for {label}: {actual} != {count}")
    return text.replace(old, new)

# Pull only the proven UI pieces from the historical combined branch.  The rest
# stays on top of v1.0.6/main so Access Group permissions and the new theme are
# not rolled back.
run("git", "fetch", "origin", "test/node-dashboard-combined:refs/remotes/origin/test/node-dashboard-combined")
run(
    "git", "checkout", "origin/test/node-dashboard-combined", "--",
    "app/dashboard/src/components/NodesManagementWorkspace.tsx",
    "app/dashboard/src/components/NodesModal.tsx",
    "app/dashboard/src/components/FiltersCompact.tsx",
    "app/dashboard/src/pages/Dashboard.tsx",
)

# Dashboard: keep the combined branch layout (including removal of the live
# bandwidth block) but normalize text colors to the v1.0.6 Light/Dark tokens.
p = "app/dashboard/src/pages/Dashboard.tsx"
s = read(p)
for old, new in {
    'color="gray.400"': 'color="var(--panel-text-muted)"',
    'color="gray.300"': 'color="var(--panel-text-body)"',
    'color="gray.500"': 'color="var(--panel-text-muted)"',
    'color="primary.300"': 'color="var(--panel-accent)"',
}.items():
    s = s.replace(old, new)
if "NodeBandwidthPanel" in s:
    raise RuntimeError("NodeBandwidthPanel must not remain on Dashboard")
if "UserManagementControls" not in s:
    raise RuntimeError("combined dashboard controls were not imported")
write(p, s)

# Filters: direct sort buttons + Admin dropdown from the combined branch, but
# with the release palette/radius system instead of dark-only Chakra shades.
p = "app/dashboard/src/components/FiltersCompact.tsx"
s = read(p)
status_re = re.compile(r"const StatusButton: FC<\{.*?\n\);\n\nconst sortOptions", re.S)
status_component = '''const statusPalettes = {
  primary: { color: "var(--panel-accent)", bg: "var(--panel-accent-soft)", border: "var(--panel-accent-border)" },
  green: { color: "var(--panel-success)", bg: "var(--panel-success-soft)", border: "var(--panel-success-border)" },
  red: { color: "var(--panel-danger)", bg: "var(--panel-danger-soft)", border: "var(--panel-danger-border)" },
  orange: { color: "var(--panel-warning)", bg: "var(--panel-warning-soft)", border: "var(--panel-warning-border)" },
  gray: { color: "var(--panel-text-muted)", bg: "var(--panel-muted-soft)", border: "var(--panel-border)" },
} as const;

const StatusButton: FC<{
  active: boolean;
  label: string;
  onClick: () => void;
  tone?: keyof typeof statusPalettes;
}> = ({ active, label, onClick, tone = "primary" }) => {
  const palette = statusPalettes[tone];
  return (
    <Button
      size="sm"
      h="36px"
      px={3.5}
      borderRadius="12px"
      variant="outline"
      borderColor={active ? palette.border : "var(--panel-border)"}
      bg={active ? palette.bg : "var(--panel-surface)"}
      color={active ? palette.color : "var(--panel-text-body)"}
      fontSize="11px"
      fontWeight="750"
      whiteSpace="nowrap"
      onClick={onClick}
      transition="transform .14s ease, border-color .14s ease, background .14s ease"
      _hover={{ transform: "translateY(-1px)", borderColor: palette.border, color: palette.color }}
      _active={{ transform: "translateY(0)" }}
    >
      {label}
    </Button>
  );
};

const sortOptions'''
s, n = status_re.subn(status_component, s, count=1)
if n != 1:
    raise RuntimeError("StatusButton block not found")
s = s.replace('borderRadius="8px"', 'borderRadius="12px"')
s = s.replace('color={active ? "var(--panel-accent)" : "gray.400"}', 'color={active ? "var(--panel-accent)" : "var(--panel-text-body)"}')
s = s.replace('color="gray.500"', 'color="var(--panel-text-muted)"')
s = s.replace('borderColor={active ? "var(--panel-accent-border)" : "var(--panel-border)"}', 'borderColor={active ? "var(--panel-accent-border)" : "var(--panel-border)"}')
if "UserManagementControls" not in s or "SortButton" not in s or "همه ادمین‌ها" not in s:
    raise RuntimeError("direct sort/Admin controls missing")
write(p, s)

# Bulk actions: preserve the current backend/dialog behavior but replace the
# dropdown with direct actions.  Selected-user actions disappear when nothing
# is selected; cleanup actions stay available because they are global tools.
p = "app/dashboard/src/components/BulkUserActions.tsx"
s = read(p)
for token in ["  Menu,\n", "  MenuButton,\n", "  MenuItem,\n", "  MenuList,\n"]:
    s = s.replace(token, "")
s = s.replace("  ChevronDownIcon,\n", "")
menu_re = re.compile(r"\n\s*<Menu placement=\"bottom-end\">.*?</Menu>\n", re.S)
direct_buttons = '''
          {users.length > 0 && (
            <>
              <Button size="sm" variant="outline" color="var(--panel-success)" borderColor="var(--panel-success-border)" bg="var(--panel-success-soft)" leftIcon={<BoltIcon width="17px" aria-hidden="true" />} onClick={() => openAction(actionDefinitions[0])}>{t(actionDefinitions[0].labelKey)}</Button>
              <Button size="sm" variant="outline" color="var(--panel-warning)" borderColor="var(--panel-warning-border)" bg="var(--panel-warning-soft)" leftIcon={<NoSymbolIcon width="17px" aria-hidden="true" />} onClick={() => openAction(actionDefinitions[1])}>{t(actionDefinitions[1].labelKey)}</Button>
              <Button size="sm" variant="outline" color="var(--panel-accent)" borderColor="var(--panel-accent-border)" bg="var(--panel-accent-soft)" leftIcon={<CircleStackIcon width="17px" aria-hidden="true" />} onClick={() => openAction(actionDefinitions[2])}>{t(actionDefinitions[2].labelKey)}</Button>
              <Button size="sm" variant="outline" color="var(--panel-text-body)" borderColor="var(--panel-border)" bg="var(--panel-muted-soft)" leftIcon={<CircleStackIcon width="17px" aria-hidden="true" />} onClick={() => openAction(actionDefinitions[3])}>{t(actionDefinitions[3].labelKey)}</Button>
              <Button size="sm" variant="outline" color="var(--panel-accent)" borderColor="var(--panel-accent-border)" bg="var(--panel-accent-soft)" leftIcon={<CalendarDaysIcon width="17px" aria-hidden="true" />} onClick={() => openAction(actionDefinitions[4])}>{t(actionDefinitions[4].labelKey)}</Button>
              <Button size="sm" variant="outline" color="var(--panel-text-body)" borderColor="var(--panel-border)" bg="var(--panel-muted-soft)" leftIcon={<CalendarDaysIcon width="17px" aria-hidden="true" />} onClick={() => openAction(actionDefinitions[5])}>{t(actionDefinitions[5].labelKey)}</Button>
              <Button size="sm" variant="outline" color="var(--panel-accent)" borderColor="var(--panel-accent-border)" bg="var(--panel-accent-soft)" leftIcon={<CalendarDaysIcon width="17px" aria-hidden="true" />} onClick={() => openAction(actionDefinitions[6])}>{t(actionDefinitions[6].labelKey)}</Button>
              <Button size="sm" variant="outline" color="var(--panel-danger)" borderColor="var(--panel-danger-border)" bg="var(--panel-danger-soft)" leftIcon={<TrashIcon width="17px" aria-hidden="true" />} onClick={() => openAction(actionDefinitions[7])}>{t(actionDefinitions[7].labelKey)}</Button>
            </>
          )}
'''
s, n = menu_re.subn(direct_buttons, s, count=1)
if n != 1:
    raise RuntimeError("bulk action menu block not found")
for old, new in {
    "تعداد هدف snapshot": "تعداد کاربران هدف",
    "گزارش job:": "گزارش عملیات:",
    "Retry خطاهای قابل‌تکرار": "تلاش دوباره برای خطاهای قابل‌تکرار",
    "کاربران ادمین‌های انتخابی و subtree": "کاربران ادمین‌های انتخابی و زیرمجموعه‌های آن‌ها",
    'borderColor="whiteAlpha.200"': 'borderColor="var(--panel-border)"',
    'color="orange.200"': 'color="var(--panel-warning)"',
    'borderColor="orange.700"': 'borderColor="var(--panel-warning-border)"',
    'color="red.200"': 'color="var(--panel-danger)"',
    'borderColor="red.800"': 'borderColor="var(--panel-danger-border)"',
}.items():
    s = s.replace(old, new)
if "<Menu placement=\"bottom-end\">" in s:
    raise RuntimeError("bulk dropdown still present")
write(p, s)

# User table: keep the v1.0.6 modern table/status/progress/kebab design.  Only
# port the combined branch behavior: bulk toolbar inside the table and the
# Device Limit shield restored as a compact row action.
p = "app/dashboard/src/components/UsersTablePro.tsx"
s = read(p)
if 'import { UserDeviceLimit } from "./UserDeviceLimit";' not in s:
    s = s.replace('import { BulkUserActions } from "./BulkUserActions";\n', 'import { BulkUserActions } from "./BulkUserActions";\nimport { UserDeviceLimit } from "./UserDeviceLimit";\n')
outer_bulk_re = re.compile(r'''\n      \{!readOnly && \(\n        <Box px=\{0\} pb=\{2\.5\}>.*?\n      \)\}\n\n      (<TableContainer[^\n]*>)''', re.S)
bulk_inside = '''
      \\1
        {!readOnly && (
          <Box
            px={{ base: 2, md: 2.5 }}
            borderBottomWidth="1px"
            borderColor="var(--panel-border)"
            bg="var(--panel-nested)"
            sx={{
              "& > div:first-of-type": {
                marginTop: "0 !important",
                paddingInline: "0 !important",
                paddingBlock: "8px !important",
                border: "0 !important",
                borderRadius: "0 !important",
                background: "transparent !important",
              },
            }}
          >
            <BulkUserActions
              users={selectedUsers}
              allVisibleSelected={allVisibleSelected}
              visibleCount={users.length}
              onToggleAll={toggleAllVisible}
              onClear={() => setSelectedMap(new Map())}
            />
            {selectedUsers.length > users.filter((user) => selectedMap.has(user.username)).length && (
              <Text pb={2} color="var(--panel-warning)" fontSize="10px">
                انتخاب‌ها بین صفحه‌ها حفظ شده‌اند؛ مجموع انتخاب‌شده: {selectedUsers.length.toLocaleString("fa-IR")}
              </Text>
            )}
          </Box>
        )}
'''
s, n = outer_bulk_re.subn(bulk_inside, s, count=1)
if n != 1:
    raise RuntimeError("could not move bulk toolbar into user table")
copy_line = '                      <Action label="کپی لینک اشتراک" icon={<CopyIcon />} onClick={() => copySubscription(user)} tone="green" />'
if copy_line not in s:
    raise RuntimeError("copy action anchor missing")
s = s.replace(copy_line, copy_line + '\n                      {!readOnly && isOwner && <UserDeviceLimit user={user} compact />}')
s = s.replace('color={user.online_at ? "green.300" : "gray.600"}', 'color={user.online_at ? "var(--panel-success)" : "var(--panel-text-muted)"}')
s = s.replace('color={user.note ? "gray.300" : "gray.600"}', 'color={user.note ? "var(--panel-text-body)" : "var(--panel-text-muted)"}')
if s.index("<BulkUserActions") < s.index("<TableContainer"):
    raise RuntimeError("BulkUserActions must be inside TableContainer")
write(p, s)

# Device-limit action: compact row shield while retaining the v1.0.6 themed
# modal rather than copying the older dark-only version from the branch.
p = "app/dashboard/src/components/UserDeviceLimit.tsx"
s = read(p)
s = must_replace(s, 'export const UserDeviceLimit: FC<{ user: User }> = ({ user }) => {', '''type UserDeviceLimitProps = {\n  user: User;\n  compact?: boolean;\n};\n\nexport const UserDeviceLimit: FC<UserDeviceLimitProps> = ({ user, compact = false }) => {''', "device limit props", 1)
s = must_replace(s, '''          size="sm"\n          minW="44px"\n          h="44px"\n          borderRadius="9px"\n          variant="outline"\n          color={hasPenalty || warned ? "yellow.200" : "green.200"}\n          borderColor={hasPenalty || warned ? "rgba(234,179,8,.5)" : "rgba(34,197,94,.4)"}\n          bg={hasPenalty || warned ? "rgba(234,179,8,.08)" : "rgba(34,197,94,.06)"}\n          _hover={{ bg: hasPenalty || warned ? "rgba(234,179,8,.15)" : "rgba(34,197,94,.13)" }}''', '''          size={compact ? "xs" : "sm"}\n          minW={compact ? "30px" : "44px"}\n          w={compact ? "30px" : undefined}\n          h={compact ? "30px" : "44px"}\n          borderRadius={compact ? "10px" : "12px"}\n          variant="outline"\n          color={hasPenalty || warned ? "var(--panel-warning)" : "var(--panel-success)"}\n          borderColor={hasPenalty || warned ? "var(--panel-warning-border)" : "var(--panel-success-border)"}\n          bg={hasPenalty || warned ? "var(--panel-warning-soft)" : "var(--panel-success-soft)"}\n          _hover={{ bg: hasPenalty || warned ? "var(--panel-warning-soft)" : "var(--panel-success-soft)" }}''', "compact shield", 1)
s = s.replace('bg="rgba(2,6,23,.28)"', 'bg="var(--panel-nested)"')
s = s.replace('borderColor="rgba(148,163,184,.15)"', 'borderColor="var(--panel-border)"')
s = s.replace('startColor="#14231b" endColor="#243d31"', 'startColor="var(--panel-nested)" endColor="var(--panel-surface)"')
write(p, s)

# Access Groups: complete the Plans section visually and remove mixed English
# UI copy without changing API/model names or permission semantics.
p = "app/dashboard/src/components/AccessGroupManager.tsx"
s = read(p)
for old, new in {
    'toast({ title: `Access Group «${group.name}» ذخیره شد`': 'toast({ title: `گروه دسترسی «${group.name}» ذخیره شد`',
    'title: "ذخیره Access Group انجام نشد"': 'title: "ذخیره گروه دسترسی انجام نشد"',
    'toast({ title: "Access Group بایگانی شد"': 'toast({ title: "گروه دسترسی بایگانی شد"',
    'title: "بایگانی Access Group انجام نشد"': 'title: "بایگانی گروه دسترسی انجام نشد"',
    '"نام Access Group الزامی است"': '"نام گروه دسترسی الزامی است"',
    '"حداقل یک Inbound انتخاب کنید"': '"حداقل یک اینباند انتخاب کنید"',
    '`Host ID: ${missingHosts.join(", ")}`': '`شناسه هاست: ${missingHosts.join(", ")}`',
    '"برای هر Inbound حداقل یک Host فعال انتخاب کنید"': '"برای هر اینباند حداقل یک هاست فعال انتخاب کنید"',
    'گزینه‌های Access Group دریافت نشدند.': 'اطلاعات گروه‌های دسترسی دریافت نشد.',
    'Inbound، Host و Node فقط اینجا مدیریت می‌شوند. ویرایش گروه، کاربران فعال همان گروه را همگام می‌کند.': 'اینباند، هاست و نودهای هر گروه از همین بخش مدیریت می‌شوند. با ذخیره تغییرات، کاربران فعال آن گروه نیز همگام می‌شوند.',
    '"ویرایش Access Group"': '"ویرایش گروه دسترسی"',
    '"Access Group جدید"': '"گروه دسترسی جدید"',
    'انتخاب خالی هرگز به معنی همه نیست؛ فقط Node خالی یعنی بدون فیلتر Node.': 'برای اینباند و هاست انتخاب صریح لازم است؛ خالی گذاشتن نود یعنی محدودیتی روی نود اعمال نمی‌شود.',
    '<FormLabel>Nodeها</FormLabel>': '<FormLabel>نودها</FormLabel>',
    'Nodeی ثبت نشده است.': 'نودی ثبت نشده است.',
    '${draft.nodeIds.length} Node انتخاب شده': '${draft.nodeIds.length} نود انتخاب شده',
    'همه Nodeها؛ فیلتر Node اعمال نمی‌شود.': 'همه نودها؛ فیلتر نود اعمال نمی‌شود.',
    '<FormLabel>Inbound و Hostهای مجاز</FormLabel>': '<FormLabel>اینباندها و هاست‌های مجاز</FormLabel>',
    'Host فعال برای این Inbound وجود ندارد.': 'هاست فعالی برای این اینباند وجود ندارد.',
    'Inbound واجدشرایطی پیدا نشد.': 'اینباند قابل استفاده‌ای پیدا نشد.',
    'برای هر Inbound انتخاب‌شده، حداقل یک Host فعال لازم است.': 'برای هر اینباند انتخاب‌شده حداقل یک هاست فعال لازم است.',
    '"ساخت Access Group"': '"ساخت گروه دسترسی"',
    '${group.inbounds.length} Inbound': '${group.inbounds.length} اینباند',
    '${group.node_ids.length} Node': '${group.node_ids.length} نود',
    '"همه Nodeها"': '"همه نودها"',
    '`Access Group «${group.name}» بایگانی شود؟`': '`گروه دسترسی «${group.name}» بایگانی شود؟`',
    'هنوز Access Group ساخته نشده است.': 'هنوز گروه دسترسی ساخته نشده است.',
    '_dark={{ color: "gray.400" }} ': '',
    'borderRadius="8px"': 'borderRadius="12px"',
}.items():
    s = s.replace(old, new)
marker = 'const fetchAdmins = async (): Promise<ManagedAdmin[]> => {'
labels = '''const adminStatusLabel = (status?: string | null) => ({\n  ACTIVE: "فعال",\n  SUSPENDED: "تعلیق",\n  DISABLED: "غیرفعال",\n}[status || ""] || status || "نامشخص");\n\nconst nodeStatusLabel = (status?: string | null) => ({\n  connected: "متصل",\n  connecting: "در حال اتصال",\n  disabled: "غیرفعال",\n  error: "خطا",\n}[status || ""] || status || "نامشخص");\n\n'''
if labels not in s:
    s = s.replace(marker, labels + marker)
s = s.replace('{admin.account_status}</Badge>', '{adminStatusLabel(admin.account_status)}</Badge>')
s = s.replace('{node.status}</Badge>', '{nodeStatusLabel(node.status)}</Badge>')
write(p, s)

# Plans: make Access Groups a proper full-width section (not a card nested in a
# card), add a quick anchor, and normalize Persian copy.
p = "app/dashboard/src/pages/Plans.tsx"
s = read(p)
s = s.replace('نسخه‌های تغییرناپذیر، دسترسی شاخه‌ای و ساخت کاربر بدون ورود دستی محدودیت‌ها.', 'مدیریت پلن، قیمت و ساخت کاربر از یک مسیر مشخص و قابل پیگیری.')
s = s.replace('<FormLabel fontSize="xs">Access Group</FormLabel>', '<FormLabel fontSize="xs">گروه دسترسی</FormLabel>')
s = s.replace('Owner یا مدیر مجاز باید نخستین پلن را بسازد.', 'مالک پنل یا مدیر مجاز باید نخستین پلن را بسازد.')
s = s.replace('borderColor="whiteAlpha.200"', 'borderColor="var(--panel-border)"')
old_button = '{canManage && <Button minH="44px" colorScheme="primary" color="var(--panel-accent-contrast)" onClick={openCreate} isDisabled={(categories.data || []).length === 0}>پلن جدید</Button>}'
new_button = '''<HStack spacing={2} flexWrap="wrap">\n          {account.data?.role === "OWNER" && <Button as="a" href="#access-groups" minH="44px" variant="outline" borderColor="var(--panel-border)">گروه‌های دسترسی</Button>}\n          {canManage && <Button minH="44px" colorScheme="primary" color="var(--panel-accent-contrast)" onClick={openCreate} isDisabled={(categories.data || []).length === 0}>پلن جدید</Button>}\n        </HStack>'''
s = must_replace(s, old_button, new_button, "Plans action buttons", 1)
section_re = re.compile(r'''\{account\.data\?\.role === "OWNER" && \(\n        <Card mt=\{6\}.*?<AccessGroupManager />\n        </Card>\n      \)\}''', re.S)
section = '''{account.data?.role === "OWNER" && (
        <Box id="access-groups" mt={8} pt={6} borderTopWidth="1px" borderColor="var(--panel-border)">
          <Stack spacing={1} mb={5}>
            <Text color="var(--panel-accent)" fontSize="xs" fontWeight="800">دسترسی شبکه</Text>
            <Text as="h2" fontSize="xl" fontWeight="800">گروه‌های دسترسی</Text>
            <Text color="var(--panel-text-muted)" fontSize="sm">
              هر گروه مشخص می‌کند یک کاربر از کدام اینباندها، هاست‌ها و نودها استفاده کند و کدام ادمین‌ها اجازه استفاده از آن گروه را داشته باشند. شرایط مالی همچنان در خود پلن مدیریت می‌شود.
            </Text>
          </Stack>
          <AccessGroupManager />
        </Box>
      )}'''
s, n = section_re.subn(section, s, count=1)
if n != 1:
    raise RuntimeError("Access Group Plans section not found")
write(p, s)

# Release metadata.
write("VERSION", "1.0.7\n")
for path in [
    "app/__init__.py",
    "docker-compose.yml",
    "scripts/marzban.sh",
    "README.md",
    "README-fa.md",
    "tests/test_release_contract.py",
    "tests/test_installer_v1_contract.sh",
]:
    s = read(path)
    s = s.replace("v1.0.6", "v1.0.7").replace("1.0.6", "1.0.7")
    write(path, s)

release_notes = '''# Marzban v1.0.7\n\n## Dashboard and Node management\n\n- Ported the reviewed `test/node-dashboard-combined` Node Management workspace onto the current mainline without rolling back v1.0.6 Access Group or theme changes.\n- Removed the live Node Bandwidth panel from the main Dashboard; live bandwidth remains available inside Node Management where it belongs.\n- Reorganized user management controls for RTL: direct sort buttons, Admin-only dropdown filtering, compact Search / status / create / refresh controls.\n- Moved bulk-user actions into the table header area, converted selected-user bulk operations to direct buttons, and hide them until at least one user is selected.\n- Restored the compact Device Limit shield/warning action in each applicable user row while keeping the modern kebab menu for secondary row actions.\n\n## Access Groups and UI polish\n\n- Completed the Access Group section under Plans with a dedicated full-width section and quick navigation link.\n- Normalized mixed Persian/English labels for Access Groups, Nodes, Inbounds and Hosts while preserving technical values and API behavior.\n- Preserved the v1.0.6 Light/Dark palette, soft status badges, thin traffic progress bars, 12/16px radius system and current Admin Management architecture.\n\n## Verification\n\n- Dashboard TypeScript/Vite production build.\n- Access Group and Admin UI contract checks.\n- v1.0.7 Node/Dashboard UI contract.\n- Official MySQL 8.0 and 26.7.0 regression/migration/backup/rollback compatibility workflow before release.\n'''
write("docs/RELEASE_NOTES_v1.0.7.md", release_notes)

# v1.0.7 contract is the current dashboard release contract.  Keep the v1.0.6
# filename as a compatibility entrypoint because the permanent Release workflow
# already invokes it.
v107 = r'''const assert = require("node:assert/strict");
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

assert.ok(!bulk.includes("<Menu placement=\"bottom-end\">"), "bulk operations must not use a dropdown");
assert.ok(bulk.includes("users.length > 0"), "selected-user bulk controls must stay hidden without a selection");
for (const key of ["bulkActivate", "bulkDeactivate", "bulkAddVolume", "bulkSubtractVolume", "bulkAddDays", "bulkSubtractDays", "bulkAddVolumeAndDays", "bulkDeleteSelected"]) assert.ok(bulk.includes(key), `bulk action missing: ${key}`);
assert.ok(!bulk.includes("Retry خطاهای") && !bulk.includes("گزارش job") && !bulk.includes("هدف snapshot"), "mixed UI copy must be normalized");

assert.ok(users.includes("<Progress") && users.includes('h="4px"'), "thin traffic progress bar must be preserved");
assert.ok(users.includes('boxSize="6px"') && users.includes('borderColor={meta.border}'), "soft status badge + dot must be preserved");
assert.ok(users.includes("<MenuButton") && users.includes("عملیات بیشتر"), "secondary row actions stay in kebab menu");
assert.ok(users.includes("<UserDeviceLimit user={user} compact"), "Device Limit shield must be restored in user rows");
assert.ok(device.includes("compact?: boolean") && device.includes('minW={compact ? "30px" : "44px"}'));
assert.ok(users.indexOf("<BulkUserActions") > users.indexOf("<TableContainer"), "bulk toolbar must live inside the table container");
assert.ok(users.includes('data-disabled={user.status === "disabled"'));

assert.ok(plans.includes('id="access-groups"') && plans.includes("گروه‌های دسترسی"));
assert.ok(plans.includes("<AccessGroupManager />") && !settings.includes("<AccessGroupManager />"));
for (const oldCopy of ["Access Group جدید", "Nodeها", "Inbound و Hostهای مجاز", "هنوز Access Group ساخته نشده"]) assert.ok(!groups.includes(oldCopy), `mixed Access Group copy remains: ${oldCopy}`);
assert.ok(header.includes(">پیکربندی</Button>"));
assert.ok(adminTable.includes("<StatusPill") && adminTable.includes("عملیات سریع"), "modular Admin UI must remain intact");

console.log("v1.0.7 UI/UX contract: assertions passed");
'''
write("app/dashboard/scripts/test-v107-ui.cjs", v107)
write("app/dashboard/scripts/test-v106-ui.cjs", 'require("./test-v107-ui.cjs");\n')

# Guardrails against accidentally pulling unrelated historical files.
status = subprocess.check_output(["git", "status", "--short"], cwd=ROOT, text=True)
print(status)
