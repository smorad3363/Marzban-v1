from pathlib import Path
import re

ROOT = Path('.')


def read(path: str) -> str:
    return (ROOT / path).read_text(encoding='utf-8')


def write(path: str, text: str) -> None:
    (ROOT / path).write_text(text, encoding='utf-8')


def replace_once(path: str, old: str, new: str) -> None:
    text = read(path)
    if old not in text:
        raise SystemExit(f'missing expected block in {path}: {old[:120]!r}')
    text = text.replace(old, new, 1)
    write(path, text)


# Header: remove reset-all usage, remove default sidebar branding, and bind
# sidebar palette explicitly to Chakra's active color mode.
path = 'app/dashboard/src/components/Header.tsx'
text = read(path)
text = text.replace('  DocumentMinusIcon,\n', '')
text = text.replace('import { BrandMark } from "./BrandMark";\n', '')
text = text.replace('const ResetUsageIcon = chakra(DocumentMinusIcon, iconProps);\n', '')
text = text.replace(
    '  const { onEditingHosts, onResetAllUsage, onEditingNodes, onShowingNodesUsage } = useDashboard();',
    '  const { onEditingHosts, onEditingNodes, onShowingNodesUsage } = useDashboard();'
)
text = text.replace(
    '  const [mobileMenuOpen, setMobileMenuOpen] = useState(false);\n',
    '  const [mobileMenuOpen, setMobileMenuOpen] = useState(false);\n'
    '  const sidebarLogo = branding.logo_url || userData.logo_url || null;\n'
    '  const sidebarName = (branding.panel_name || "").trim();\n'
    '  const showSidebarName = Boolean(sidebarName && sidebarName !== "Operations Console");\n'
    '  const showSidebarBrand = Boolean(sidebarLogo || showSidebarName);\n'
)
text = text.replace(
    '    <Flex\n      as="aside"\n',
    '    <Flex\n      as="aside"\n      className="operations-sidebar"\n      data-color-mode={colorMode}\n'
)
old_brand = '''      <HStack justify="space-between" align="center" gap={3}>
        <HStack spacing={3} minW={0}>
          {branding.logo_url || userData.logo_url
            ? <Image src={branding.logo_url || userData.logo_url || undefined} alt={`${branding.panel_name} logo`} boxSize={{ base: "38px", lg: "46px" }} objectFit="contain" borderRadius="10px" />
            : <BrandMark aria-hidden="true" boxSize={{ base: "38px", lg: "46px" }} filter="none" />}
          <Box minW={0}>
            <Text fontSize="sm" fontWeight="800" letterSpacing="-0.01em" color="var(--panel-text)" noOfLines={1}>{branding.panel_name}</Text>
            <Text fontSize="xs" color="var(--panel-text-muted)" mt="1px" noOfLines={1}>Operations workspace</Text>
          </Box>
        </HStack>
        <HStack display={{ base: "flex", lg: "none" }} spacing={1} flexShrink={0}>
'''
new_brand = '''      <HStack justify={showSidebarBrand ? "space-between" : "flex-end"} align="center" gap={3}>
        {showSidebarBrand && (
          <HStack spacing={3} minW={0}>
            {sidebarLogo && (
              <Image
                src={sidebarLogo}
                alt={showSidebarName ? `${sidebarName} logo` : "لوگوی پنل"}
                boxSize={{ base: "38px", lg: "46px" }}
                objectFit="contain"
                borderRadius="10px"
              />
            )}
            {showSidebarName && (
              <Text fontSize="sm" fontWeight="800" letterSpacing="-0.01em" color="var(--panel-text)" noOfLines={1}>
                {sidebarName}
              </Text>
            )}
          </HStack>
        )}
        <HStack display={{ base: "flex", lg: "none" }} spacing={1} flexShrink={0}>
'''
if old_brand not in text:
    raise SystemExit('Header branding block not found')
text = text.replace(old_brand, new_brand, 1)
text = text.replace('            <ActionButton icon={<ResetUsageIcon />} label={t("resetAllUsage")} onClick={() => onResetAllUsage(true)} danger />\n', '')
write(path, text)

# Global configuration overlays: mount them in AppShell so sidebar actions work
# on Users, Plans, Admins, Audit, Device Limits, and Settings alike.
write('app/dashboard/src/components/AppShell.tsx', '''import { Box, Flex } from "@chakra-ui/react";
import useGetUser from "hooks/useGetUser";
import { FC, PropsWithChildren } from "react";
import { CoreSettingsModal } from "./CoreSettingsModal";
import { Footer } from "./Footer";
import { Header } from "./Header";
import { HostsDialog } from "./HostsDialog";
import { NodesDialog } from "./NodesModal";
import { NodesUsage } from "./NodesUsage";

export const AppShell: FC<PropsWithChildren> = ({ children }) => {
  const { userData, getUserIsPending } = useGetUser();
  const isOwner = !getUserIsPending && (userData.is_sudo || userData.role === "OWNER");

  return (
    <>
      <Flex minH="100vh" align="stretch" direction={{ base: "column", lg: "row" }} className="operations-shell">
        <Header />
        <Flex
          as="main"
          minW={0}
          flex="1"
          direction="column"
          id="main-content"
          px={{ base: 4, md: 7, xl: 9 }}
          py={{ base: 5, md: 7 }}
        >
          <Box w="full" maxW="none" minW={0} flex="1">
            {children}
          </Box>
          <Footer mt={8} />
        </Flex>
      </Flex>

      {isOwner && (
        <>
          <HostsDialog />
          <NodesDialog />
          <NodesUsage />
          <CoreSettingsModal />
        </>
      )}
    </>
  );
};
''')

# Dashboard: no duplicate global overlays and no rotating slogan copy.
path = 'app/dashboard/src/pages/Dashboard.tsx'
text = read(path)
for line in [
    'import { CoreSettingsModal } from "components/CoreSettingsModal";\n',
    'import { HostsDialog } from "components/HostsDialog";\n',
    'import { NodesDialog } from "components/NodesModal";\n',
    'import { NodesUsage } from "components/NodesUsage";\n',
    'import { ResetAllUsageModal } from "components/ResetAllUsageModal";\n',
]:
    text = text.replace(line, '')
text = re.sub(
    r'const shortMessages = \[.*?\n\};\n\n(?=const calendarParts)',
    '',
    text,
    flags=re.S,
)
text = text.replace('              <Text color="var(--panel-text-muted)" fontSize="11px">{messageForToday()}</Text>\n', '')
text = text.replace('''      {isOwner && (
        <>
          <HostsDialog />
          <NodesDialog />
          <NodesUsage />
          <ResetAllUsageModal />
          <CoreSettingsModal />
        </>
      )}
''', '')
write(path, text)

# Bulk actions: preserve every operation but collapse the toolbar into compact
# menus (status / credit / cleanup) plus one explicit destructive action.
path = 'app/dashboard/src/components/BulkUserActions.tsx'
text = read(path)
text = text.replace(
    '  ModalOverlay,\n  Select,\n',
    '  ModalOverlay,\n  Menu,\n  MenuButton,\n  MenuItem,\n  MenuList,\n  Select,\n'
)
text = text.replace(
    '  CalendarDaysIcon,\n',
    '  CalendarDaysIcon,\n  ChevronDownIcon,\n'
)
pattern = re.compile(r'        <HStack spacing=\{2\} flexWrap="wrap" justify="flex-end">.*?        </HStack>\n      </Flex>', re.S)
replacement = '''        <HStack spacing={2} flexWrap="wrap" justify="flex-end">
          <Menu placement="bottom-end">
            <MenuButton
              as={Button}
              size="sm"
              variant="outline"
              color="var(--panel-text-body)"
              borderColor="var(--panel-border)"
              rightIcon={<ChevronDownIcon width="15px" aria-hidden="true" />}
            >
              پاک‌سازی
            </MenuButton>
            <MenuList minW="220px" bg="var(--panel-surface)" borderColor="var(--panel-border)" boxShadow="var(--shadow-elevated)">
              <MenuItem bg="transparent" _hover={{ bg: "var(--panel-row-hover)" }} icon={<TrashIcon width="16px" />} onClick={trialCleanupDialog.onOpen}>
                پاک‌سازی اکانت تست
              </MenuItem>
              {userData.is_sudo && (
                <MenuItem bg="transparent" color="var(--panel-danger)" _hover={{ bg: "var(--panel-danger-soft)" }} icon={<TrashIcon width="16px" />} onClick={cleanupDialog.onOpen}>
                  {t("usersTable.cleanupExpired")}
                </MenuItem>
              )}
            </MenuList>
          </Menu>

          {users.length > 0 && (
            <>
              <Menu placement="bottom-end">
                <MenuButton
                  as={Button}
                  size="sm"
                  variant="outline"
                  color="var(--panel-success)"
                  borderColor="var(--panel-success-border)"
                  bg="var(--panel-success-soft)"
                  rightIcon={<ChevronDownIcon width="15px" aria-hidden="true" />}
                >
                  وضعیت
                </MenuButton>
                <MenuList minW="210px" bg="var(--panel-surface)" borderColor="var(--panel-border)" boxShadow="var(--shadow-elevated)">
                  <MenuItem bg="transparent" _hover={{ bg: "var(--panel-success-soft)" }} icon={<BoltIcon width="16px" />} onClick={() => openAction(actionDefinitions[0])}>
                    {t(actionDefinitions[0].labelKey)}
                  </MenuItem>
                  <MenuItem bg="transparent" _hover={{ bg: "var(--panel-warning-soft)" }} icon={<NoSymbolIcon width="16px" />} onClick={() => openAction(actionDefinitions[1])}>
                    {t(actionDefinitions[1].labelKey)}
                  </MenuItem>
                </MenuList>
              </Menu>

              <Menu placement="bottom-end">
                <MenuButton
                  as={Button}
                  size="sm"
                  variant="outline"
                  color="var(--panel-accent)"
                  borderColor="var(--panel-accent-border)"
                  bg="var(--panel-accent-soft)"
                  rightIcon={<ChevronDownIcon width="15px" aria-hidden="true" />}
                >
                  اعتبار
                </MenuButton>
                <MenuList minW="230px" bg="var(--panel-surface)" borderColor="var(--panel-border)" boxShadow="var(--shadow-elevated)">
                  <MenuItem bg="transparent" _hover={{ bg: "var(--panel-row-hover)" }} icon={<CircleStackIcon width="16px" />} onClick={() => openAction(actionDefinitions[2])}>{t(actionDefinitions[2].labelKey)}</MenuItem>
                  <MenuItem bg="transparent" _hover={{ bg: "var(--panel-row-hover)" }} icon={<CircleStackIcon width="16px" />} onClick={() => openAction(actionDefinitions[3])}>{t(actionDefinitions[3].labelKey)}</MenuItem>
                  <Divider />
                  <MenuItem bg="transparent" _hover={{ bg: "var(--panel-row-hover)" }} icon={<CalendarDaysIcon width="16px" />} onClick={() => openAction(actionDefinitions[4])}>{t(actionDefinitions[4].labelKey)}</MenuItem>
                  <MenuItem bg="transparent" _hover={{ bg: "var(--panel-row-hover)" }} icon={<CalendarDaysIcon width="16px" />} onClick={() => openAction(actionDefinitions[5])}>{t(actionDefinitions[5].labelKey)}</MenuItem>
                  <MenuItem bg="transparent" _hover={{ bg: "var(--panel-row-hover)" }} icon={<CalendarDaysIcon width="16px" />} onClick={() => openAction(actionDefinitions[6])}>{t(actionDefinitions[6].labelKey)}</MenuItem>
                </MenuList>
              </Menu>

              <Button
                size="sm"
                variant="outline"
                color="var(--panel-danger)"
                borderColor="var(--panel-danger-border)"
                bg="var(--panel-danger-soft)"
                leftIcon={<TrashIcon width="17px" aria-hidden="true" />}
                onClick={() => openAction(actionDefinitions[7])}
              >
                {t(actionDefinitions[7].labelKey)}
              </Button>

              <IconButton
                size="sm"
                variant="ghost"
                aria-label={t("usersTable.deselectAll")}
                icon={<XMarkIcon width="18px" aria-hidden="true" />}
                onClick={onClear}
              />
            </>
          )}
        </HStack>
      </Flex>'''
text, count = pattern.subn(replacement, text, count=1)
if count != 1:
    raise SystemExit(f'Bulk toolbar replacement count: {count}')
write(path, text)

# Modal close button must always sit above editor/header controls and accept clicks.
path = 'app/dashboard/chakra.config.ts'
text = read(path)
needle = '        footer: { borderColor: "var(--panel-border)" },\n'
insert = '''        footer: { borderColor: "var(--panel-border)" },
        closeButton: {
          top: 3,
          right: 3,
          zIndex: 30,
          pointerEvents: "auto",
          color: "var(--panel-text-body)",
          bg: "var(--panel-nested)",
          border: "1px solid",
          borderColor: "var(--panel-border)",
          _hover: { bg: "var(--panel-row-hover)", color: "var(--panel-text)" },
        },
'''
if needle not in text:
    raise SystemExit('Modal footer theme block not found')
text = text.replace(needle, insert, 1)
write(path, text)

# Explicit sidebar mode tokens prevent a dark navigation rail from surviving a
# Light theme switch. Also harden the modal close-button click layer.
path = 'app/dashboard/src/index.scss'
text = read(path)
marker = '\n\nbody {\n'
css = '''

.operations-sidebar[data-color-mode="light"] {
  --panel-sidebar: #F1F5F9;
  --panel-nested: #F1F5F9;
  --panel-border: #E2E8F0;
  --panel-border-strong: #CBD5E1;
  --panel-text: #0F172A;
  --panel-text-body: #334155;
  --panel-text-muted: #64748B;
  --panel-row-hover: rgba(37, 99, 235, .055);
  background: #F1F5F9 !important;
  color: #0F172A !important;
}

.operations-sidebar[data-color-mode="dark"] {
  --panel-sidebar: #0F1420;
  --panel-nested: #0F1420;
  --panel-border: #1F2937;
  --panel-border-strong: #334155;
  --panel-text: #F1F5F9;
  --panel-text-body: #CBD5E1;
  --panel-text-muted: #7C8AA0;
  --panel-row-hover: rgba(59, 130, 246, .075);
  background: #0F1420 !important;
  color: #F1F5F9 !important;
}

.chakra-modal__close-btn {
  z-index: 30 !important;
  pointer-events: auto !important;
}
'''
if marker not in text:
    raise SystemExit('index.scss body marker not found')
text = text.replace(marker, css + marker, 1)
write(path, text)

# Version metadata and immutable compose image.
write('VERSION', '1.0.8\n')
path = 'docker-compose.yml'
text = read(path)
if 'ghcr.io/smorad3363/marzban-v1:v1.0.7' not in text:
    raise SystemExit('expected v1.0.7 compose image not found')
text = text.replace('ghcr.io/smorad3363/marzban-v1:v1.0.7', 'ghcr.io/smorad3363/marzban-v1:v1.0.8', 1)
write(path, text)

# Keep a focused contract with the release so future UI work cannot silently
# reintroduce these exact regressions.
write('app/dashboard/scripts/test-v108-ui.cjs', r'''const fs = require("fs");
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
''')

# Release notes are inserted immediately after the document introduction.
path = 'RELEASES.md'
text = read(path)
heading = '## v1.0.8 UI reliability and navigation cleanup\n'
if heading not in text:
    anchor = 'Older version and SHA tags remain available and\nare not replaced by a later release.\n\n'
    if anchor not in text:
        raise SystemExit('RELEASES.md anchor not found')
    notes = '''## v1.0.8 UI reliability and navigation cleanup

This release fixes the dashboard UI regressions reported after v1.0.7. Bulk User
actions are grouped into compact Status, Credit, and Cleanup menus without
removing any operation. The Light theme now forces the navigation rail to the
light palette, configuration dialogs are mounted globally so Core/Host/Node
controls work from every dashboard page, and the reset-all-usage shortcut is
removed from configuration navigation. Modal close buttons are placed above
editor controls and remain directly clickable. The rotating dashboard slogan and
default Operations Console / Operations workspace branding are no longer shown
in the sidebar when no custom branding is configured.

Update to this release:

```bash
marzban update --version v1.0.8
```

Fresh-install this release with MySQL:

```bash
sudo bash -c "$(curl -fsSL https://raw.githubusercontent.com/smorad3363/Marzban-v1/v1.0.8/scripts/marzban.sh)" @ install --version v1.0.8 --database mysql
```

'''
    text = text.replace(anchor, anchor + notes, 1)
write(path, text)

print('v1.0.8 source patch applied')
