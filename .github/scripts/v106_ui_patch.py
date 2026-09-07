from pathlib import Path
import re


def read(path: str) -> str:
    return Path(path).read_text(encoding="utf-8")


def write(path: str, value: str) -> None:
    Path(path).write_text(value, encoding="utf-8")


def replace_once(value: str, old: str, new: str, label: str) -> str:
    count = value.count(old)
    if count != 1:
        raise RuntimeError(f"{label}: expected exactly one match, got {count}")
    return value.replace(old, new, 1)


# ---------------------------------------------------------------------------
# Chakra design system: one visual language, only light/dark color mode.
# ---------------------------------------------------------------------------
write("app/dashboard/chakra.config.ts", r'''import { extendTheme } from "@chakra-ui/react";

export const theme = extendTheme({
  config: {
    initialColorMode: "dark",
    useSystemColorMode: false,
  },
  shadows: {
    outline: "0 0 0 3px rgba(37, 99, 235, 0.22)",
    panel: "0 1px 2px rgba(15, 23, 42, .04), 0 12px 30px rgba(15, 23, 42, .07)",
    elevated: "0 18px 48px rgba(2, 6, 23, .20)",
  },
  fonts: {
    heading: `Fira Sans, Inter, -apple-system, BlinkMacSystemFont, Segoe UI, sans-serif`,
    body: `Fira Sans, Inter, -apple-system, BlinkMacSystemFont, Segoe UI, sans-serif`,
    mono: `Fira Code, IBM Plex Mono, Consolas, monospace`,
  },
  colors: {
    primary: {
      50: "#EFF6FF",
      100: "#DBEAFE",
      200: "#BFDBFE",
      300: "#93C5FD",
      400: "#60A5FA",
      500: "#3B82F6",
      600: "#2563EB",
      700: "#1D4ED8",
      800: "#1E40AF",
      900: "#1E3A8A",
    },
  },
  styles: {
    global: {
      body: {
        bg: "var(--panel-bg)",
        color: "var(--panel-text)",
        lineHeight: "1.55",
      },
      'html[lang^="fa"]': {
        "--chakra-fonts-heading": `Vazirmatn, Fira Sans, sans-serif`,
        "--chakra-fonts-body": `Vazirmatn, Fira Sans, sans-serif`,
      },
      "::selection": {
        bg: "primary.100",
        color: "#0F172A",
      },
    },
  },
  components: {
    Button: {
      baseStyle: {
        borderRadius: "12px",
        fontWeight: "650",
        transitionProperty: "background-color, border-color, color, transform, box-shadow",
        transitionDuration: "140ms",
      },
      sizes: {
        sm: { minH: "38px", px: 3.5 },
        md: { minH: "44px", px: 4 },
      },
    },
    Card: {
      baseStyle: {
        container: {
          bg: "var(--panel-surface)",
          color: "var(--panel-text)",
          borderColor: "var(--panel-border)",
          borderRadius: "16px",
          boxShadow: "var(--shadow-panel)",
        },
      },
    },
    Modal: {
      baseStyle: {
        dialog: {
          bg: "var(--panel-surface)",
          color: "var(--panel-text)",
          borderWidth: "1px",
          borderColor: "var(--panel-border)",
          borderRadius: "16px",
          boxShadow: "var(--shadow-elevated)",
        },
        header: { borderColor: "var(--panel-border)" },
        footer: { borderColor: "var(--panel-border)" },
      },
    },
    Drawer: {
      baseStyle: {
        dialog: {
          bg: "var(--panel-surface)",
          color: "var(--panel-text)",
          borderColor: "var(--panel-border)",
        },
      },
    },
    Alert: {
      baseStyle: {
        container: {
          borderRadius: "12px",
          fontSize: "sm",
        },
      },
    },
    Badge: {
      baseStyle: {
        borderRadius: "999px",
        textTransform: "none",
        fontWeight: "700",
      },
    },
    Select: {
      baseStyle: {
        field: {
          bg: "var(--panel-surface)",
          color: "var(--panel-text)",
          borderColor: "var(--panel-border-strong)",
          borderRadius: "12px",
          _hover: { borderColor: "var(--panel-accent-border)" },
          _focusVisible: {
            borderColor: "var(--panel-accent)",
            boxShadow: "0 0 0 2px var(--panel-accent-soft)",
          },
        },
      },
      sizes: {
        sm: { field: { minH: "42px", fontSize: "sm", px: 3, paddingInlineEnd: 8 } },
        md: { field: { minH: "44px", fontSize: "sm", px: 3, paddingInlineEnd: 8 } },
      },
    },
    FormHelperText: {
      baseStyle: {
        fontSize: "xs",
        color: "var(--panel-text-muted)",
      },
    },
    FormLabel: {
      baseStyle: {
        fontSize: "sm",
        fontWeight: "600",
        mb: "1",
        lineHeight: "1.7",
        whiteSpace: "normal",
        overflowWrap: "anywhere",
        color: "var(--panel-text-body)",
      },
    },
    Input: {
      baseStyle: {
        field: {
          borderRadius: "12px",
          bg: "var(--panel-surface)",
          color: "var(--panel-text)",
          borderColor: "var(--panel-border-strong)",
          _placeholder: { color: "var(--panel-text-muted)" },
          _hover: { borderColor: "var(--panel-accent-border)" },
          _focusVisible: {
            boxShadow: "0 0 0 2px var(--panel-accent-soft)",
            borderColor: "var(--panel-accent)",
          },
        },
      },
      sizes: {
        sm: { field: { minH: "42px", fontSize: "sm", px: 3 } },
        md: { field: { minH: "44px", fontSize: "sm", px: 3 } },
      },
    },
    Textarea: {
      baseStyle: {
        borderRadius: "12px",
        bg: "var(--panel-surface)",
        color: "var(--panel-text)",
        borderColor: "var(--panel-border-strong)",
        lineHeight: "1.8",
        _placeholder: { color: "var(--panel-text-muted)" },
        _hover: { borderColor: "var(--panel-accent-border)" },
        _focusVisible: { borderColor: "var(--panel-accent)", boxShadow: "0 0 0 2px var(--panel-accent-soft)" },
      },
    },
    Table: {
      baseStyle: {
        table: {
          borderCollapse: "separate",
          borderSpacing: 0,
        },
        thead: {
          bg: "var(--panel-nested)",
        },
        th: {
          bg: "var(--panel-nested)",
          color: "var(--panel-text-muted)",
          fontSize: "11px",
          fontWeight: "600",
          letterSpacing: "0",
          textTransform: "none",
          px: 4,
          py: 3,
          borderBottom: "0",
        },
        td: {
          px: 4,
          py: 4,
          color: "var(--panel-text-body)",
          borderBottom: "0",
          transition: "background-color .14s ease, opacity .14s ease",
        },
        tbody: {
          tr: {
            "&:nth-of-type(even) > td": { bg: "var(--panel-row-alt)" },
            "&:hover > td": { bg: "var(--panel-row-hover)" },
          },
        },
      },
    },
  },
});
''')

# ---------------------------------------------------------------------------
# Global color tokens from the approved palettes.
# ---------------------------------------------------------------------------
scss_path = "app/dashboard/src/index.scss"
scss = read(scss_path)
new_tokens = r''':root {
  --panel-bg: #F8FAFC;
  --panel-surface: #FFFFFF;
  --panel-sidebar: #F1F5F9;
  --panel-nested: #F1F5F9;
  --panel-border: #E2E8F0;
  --panel-border-strong: #CBD5E1;
  --panel-text: #0F172A;
  --panel-text-body: #334155;
  --panel-text-muted: #64748B;
  --panel-accent: #2563EB;
  --panel-accent-hover: #1D4ED8;
  --panel-accent-contrast: #FFFFFF;
  --panel-accent-soft: rgba(37, 99, 235, .08);
  --panel-accent-soft-strong: rgba(37, 99, 235, .13);
  --panel-accent-border: rgba(37, 99, 235, .28);
  --panel-success: #16A34A;
  --panel-success-soft: rgba(22, 163, 74, .08);
  --panel-success-border: rgba(22, 163, 74, .30);
  --panel-warning: #D97706;
  --panel-warning-soft: rgba(217, 119, 6, .08);
  --panel-warning-border: rgba(217, 119, 6, .30);
  --panel-danger: #DC2626;
  --panel-danger-soft: rgba(220, 38, 38, .07);
  --panel-danger-border: rgba(220, 38, 38, .28);
  --panel-info: #0891B2;
  --panel-info-soft: rgba(8, 145, 178, .08);
  --panel-info-border: rgba(8, 145, 178, .28);
  --panel-muted-soft: rgba(100, 116, 139, .08);
  --panel-row-alt: rgba(241, 245, 249, .62);
  --panel-row-hover: rgba(37, 99, 235, .055);
  --radius-panel: 16px;
  --radius-control: 12px;
  --shadow-panel: 0 1px 2px rgba(15, 23, 42, .04), 0 12px 30px rgba(15, 23, 42, .06);
  --shadow-elevated: 0 18px 48px rgba(15, 23, 42, .14);
  --shadow-row: 0 1px 2px rgba(15, 23, 42, .035);
}

.chakra-ui-dark {
  --panel-bg: #0B0F19;
  --panel-surface: #131826;
  --panel-sidebar: #0F1420;
  --panel-nested: #0F1420;
  --panel-border: #1F2937;
  --panel-border-strong: #334155;
  --panel-text: #F1F5F9;
  --panel-text-body: #CBD5E1;
  --panel-text-muted: #7C8AA0;
  --panel-accent: #3B82F6;
  --panel-accent-hover: #60A5FA;
  --panel-accent-contrast: #FFFFFF;
  --panel-accent-soft: rgba(59, 130, 246, .10);
  --panel-accent-soft-strong: rgba(59, 130, 246, .16);
  --panel-accent-border: rgba(96, 165, 250, .30);
  --panel-success: #22C55E;
  --panel-success-soft: rgba(34, 197, 94, .09);
  --panel-success-border: rgba(34, 197, 94, .30);
  --panel-warning: #F59E0B;
  --panel-warning-soft: rgba(245, 158, 11, .09);
  --panel-warning-border: rgba(245, 158, 11, .30);
  --panel-danger: #EF4444;
  --panel-danger-soft: rgba(239, 68, 68, .09);
  --panel-danger-border: rgba(239, 68, 68, .30);
  --panel-info: #22D3EE;
  --panel-info-soft: rgba(34, 211, 238, .09);
  --panel-info-border: rgba(34, 211, 238, .28);
  --panel-muted-soft: rgba(124, 138, 160, .09);
  --panel-row-alt: rgba(15, 20, 32, .56);
  --panel-row-hover: rgba(59, 130, 246, .075);
  --shadow-panel: 0 1px 2px rgba(0, 0, 0, .20), 0 12px 30px rgba(0, 0, 0, .16);
  --shadow-elevated: 0 18px 48px rgba(0, 0, 0, .28);
  --shadow-row: 0 1px 2px rgba(0, 0, 0, .12);
}
'''
scss, n = re.subn(r":root \{.*?\}\n\n\.chakra-ui-dark \{.*?\}\n", new_tokens, scss, count=1, flags=re.S)
if n != 1:
    raise RuntimeError("index.scss token blocks were not found")
scss, n = re.subn(
    r"body \{\n  background-color: var\(--panel-bg\) !important;.*?\n\}",
    "body {\n  background-color: var(--panel-bg) !important;\n  color: var(--panel-text) !important;\n  background-image: none;\n}",
    scss,
    count=1,
    flags=re.S,
)
if n != 1:
    raise RuntimeError("index.scss body block was not found")
scss += r'''

/* v1.0.6 unified visual language */
.chakra-card,
.chakra-modal__content,
.chakra-drawer__content {
  background: var(--panel-surface) !important;
  color: var(--panel-text) !important;
  border-color: var(--panel-border) !important;
  border-radius: var(--radius-panel) !important;
}

.chakra-button,
.chakra-input,
.chakra-select,
.chakra-textarea,
.chakra-menu__menuitem {
  border-radius: var(--radius-control) !important;
}

.chakra-table__container {
  border-radius: var(--radius-panel) !important;
}

.chakra-table th {
  color: var(--panel-text-muted) !important;
  font-weight: 600 !important;
  letter-spacing: 0 !important;
  text-transform: none !important;
  border-bottom: 0 !important;
}

.chakra-table tbody td {
  border-bottom: 0 !important;
}

.chakra-table tbody tr:nth-of-type(even) > td {
  background: var(--panel-row-alt);
}

.chakra-table tbody tr:hover > td {
  background: var(--panel-row-hover);
}

.chakra-table tbody tr[data-selected="true"] > td {
  background: var(--panel-accent-soft) !important;
}

.chakra-table tbody tr[data-disabled="true"] > td {
  opacity: .62;
}
'''
write(scss_path, scss)

index_path = "app/dashboard/src/index.tsx"
index = read(index_path)
index = replace_once(
    index,
    'document.documentElement.dataset.panelTheme = document.documentElement.dataset.panelTheme || "heisenberg";',
    'document.documentElement.dataset.panelTheme = "standard";',
    "index.tsx panel theme",
)
write(index_path, index)

# ---------------------------------------------------------------------------
# Branding controls: logo only. Chakra color mode is now the single theme axis.
# ---------------------------------------------------------------------------
write("app/dashboard/src/components/BrandingControls.tsx", r'''import { HStack, IconButton, Input, Text, Tooltip, useToast } from "@chakra-ui/react";
import { ArrowUpTrayIcon, TrashIcon } from "@heroicons/react/24/outline";
import { ChangeEvent, FC, useRef } from "react";
import { useMutation, useQueryClient } from "react-query";
import { fetch } from "service/http";
import { BrandingResponse } from "types/Admin";
import { CurrentAdminQueryKey } from "hooks/useGetUser";
import { localizedApiError } from "utils/apiError";

type Props = { hasLogo: boolean };

export const BrandingControls: FC<Props> = ({ hasLogo }) => {
  const fileRef = useRef<HTMLInputElement>(null);
  const toast = useToast();
  const queryClient = useQueryClient();
  const refresh = (data: BrandingResponse) => {
    queryClient.setQueryData(CurrentAdminQueryKey, (current: any) => ({ ...current, ...data }));
  };
  const logoMutation = useMutation(
    (body: FormData) => fetch<BrandingResponse>("/branding/logo", { method: "POST", body }),
    { onSuccess: refresh, onError: (error) => { toast({ title: "لوگو ذخیره نشد", description: localizedApiError(error), status: "error" }); } }
  );
  const removeMutation = useMutation(
    () => fetch<BrandingResponse>("/branding/logo", { method: "DELETE" }),
    { onSuccess: refresh, onError: (error) => { toast({ title: "لوگو حذف نشد", description: localizedApiError(error), status: "error" }); } }
  );
  const upload = (event: ChangeEvent<HTMLInputElement>) => {
    const file = event.target.files?.[0];
    if (!file) return;
    const body = new FormData();
    body.append("logo", file);
    logoMutation.mutate(body);
    event.target.value = "";
  };

  return (
    <HStack px={2} spacing={1.5} justify="flex-start">
      <Text fontSize="xs" color="var(--panel-text-muted)">لوگو</Text>
      <Input ref={fileRef} display="none" type="file" accept="image/png,image/jpeg,image/webp" onChange={upload} />
      <Tooltip label="انتخاب لوگو (PNG، JPG یا WebP)">
        <IconButton color="var(--panel-text-body)" aria-label="انتخاب لوگو" size="xs" variant="ghost" isLoading={logoMutation.isLoading} icon={<ArrowUpTrayIcon width={15} />} onClick={() => fileRef.current?.click()} />
      </Tooltip>
      {hasLogo && <Tooltip label="بازگشت به لوگوی پیش‌فرض"><IconButton aria-label="حذف لوگوی سفارشی" size="xs" variant="ghost" colorScheme="red" isLoading={removeMutation.isLoading} icon={<TrashIcon width={15} />} onClick={() => removeMutation.mutate()} /></Tooltip>}
    </HStack>
  );
};
''')

# Header: remove the second theme axis and make sidebar work in both palettes.
header_path = "app/dashboard/src/components/Header.tsx"
header = read(header_path)
header = header.replace(
    '  useEffect(() => {\n    document.documentElement.dataset.panelTheme = userData.dashboard_theme || "heisenberg";\n  }, [userData.dashboard_theme]);\n',
    "",
)
header = header.replace('<BrandingControls theme={userData.dashboard_theme || "heisenberg"} hasLogo={Boolean(userData.logo_url)} />', '<BrandingControls hasLogo={Boolean(userData.logo_url)} />')
header = header.replace('>تنظیمات</Button>', '>پیکربندی</Button>')
header = header.replace('"Light theme" : "Dark theme"', '"تم روشن" : "تم تیره"')
header = header.replace('color="white"', 'color="var(--panel-text)"')
header = header.replace('color="gray.200"', 'color="var(--panel-text-body)"')
header = header.replace('color="gray.400"', 'color="var(--panel-text-muted)"')
header = header.replace('color="gray.500"', 'color="var(--panel-text-muted)"')
header = header.replace('color="red.200"', 'color="var(--panel-danger)"')
header = header.replace('color: "red.100"', 'color: "var(--panel-danger)"')
header = header.replace('color: "white"', 'color: "var(--panel-text)"')
header = header.replace('bg: "whiteAlpha.100"', 'bg: "var(--panel-row-hover)"')
header = header.replace('bg: "whiteAlpha.200"', 'bg: "var(--panel-nested)"')
header = header.replace('borderColor="whiteAlpha.200"', 'borderColor="var(--panel-border)"')
write(header_path, header)

# ---------------------------------------------------------------------------
# Toolbar: segmented status tabs + advanced filters beside search.
# ---------------------------------------------------------------------------
write("app/dashboard/src/components/FiltersCompact.tsx", r'''import {
  Box,
  Button,
  Collapse,
  HStack,
  IconButton,
  Input,
  InputGroup,
  InputLeftElement,
  Select,
  Spinner,
  Stack,
  Text,
  Tooltip,
  chakra,
} from "@chakra-ui/react";
import {
  AdjustmentsHorizontalIcon,
  ArrowPathIcon,
  MagnifyingGlassIcon,
  PlusIcon,
} from "@heroicons/react/24/outline";
import { useDashboard } from "contexts/DashboardContext";
import useGetUser from "hooks/useGetUser";
import debounce from "lodash.debounce";
import { ChangeEvent, FC, useMemo, useState } from "react";
import { useTranslation } from "react-i18next";
import { useQuery } from "react-query";
import { fetch } from "service/http";
import { AccountSummary, AdminCapabilities } from "types/Admin";
import { CreateUserFromPlan } from "./CreateUserFromPlan";

const SearchIcon = chakra(MagnifyingGlassIcon, { baseStyle: { w: 4, h: 4 } });
const ReloadIcon = chakra(ArrowPathIcon, { baseStyle: { w: 4, h: 4 } });
const AddIcon = chakra(PlusIcon, { baseStyle: { w: 4, h: 4 } });
const AdvancedIcon = chakra(AdjustmentsHorizontalIcon, { baseStyle: { w: 4, h: 4 } });

type AdminOption = { username: string };

const control = {
  bg: "var(--panel-surface)",
  color: "var(--panel-text)",
  borderColor: "var(--panel-border)",
  _hover: { borderColor: "var(--panel-border-strong)" },
  _focusVisible: { borderColor: "var(--panel-accent)", boxShadow: "0 0 0 2px var(--panel-accent-soft)" },
} as const;

const StatusSegment: FC<{ active: boolean; label: string; onClick: () => void }> = ({ active, label, onClick }) => (
  <Button
    size="sm"
    minH="34px"
    px={{ base: 2.5, md: 3.5 }}
    borderRadius="10px"
    variant="ghost"
    bg={active ? "var(--panel-surface)" : "transparent"}
    color={active ? "var(--panel-accent)" : "var(--panel-text-body)"}
    boxShadow={active ? "var(--shadow-row)" : "none"}
    fontSize="12px"
    fontWeight={active ? "750" : "600"}
    onClick={onClick}
    _hover={{ bg: active ? "var(--panel-surface)" : "var(--panel-row-hover)", color: active ? "var(--panel-accent)" : "var(--panel-text)" }}
  >
    {label}
  </Button>
);

export const FiltersCompact: FC = () => {
  const { loading, filters, onFilterChange, refetchUsers, onCreateUser } = useDashboard();
  const { i18n } = useTranslation();
  const { userData } = useGetUser();
  const [search, setSearch] = useState(filters.search || "");
  const [planCreateOpen, setPlanCreateOpen] = useState(false);
  const [advancedOpen, setAdvancedOpen] = useState(Boolean(filters.admin));

  const account = useQuery<AccountSummary, Error>("account-summary", () => fetch("/account/summary"));
  const capabilities = useQuery<AdminCapabilities, Error>(
    ["admin-capabilities", userData.username],
    () => fetch("/admin/capabilities")
  );
  const canManageAdmins = Boolean(capabilities.data?.can_manage_admins);
  const accountActive = account.data?.account_status === "ACTIVE";
  const adminOptions = useQuery<AdminOption[], Error>(
    "user-filter-admins",
    () => fetch("/admins", { query: { limit: 1000 } }),
    { enabled: canManageAdmins, staleTime: 30000 }
  );

  const updateSearch = useMemo(
    () => debounce((value: string) => onFilterChange({ search: value, offset: 0 }), 280),
    [onFilterChange]
  );

  const setStatus = (value?: typeof filters.status) => onFilterChange({ status: value, offset: 0 });
  const changeSort = (event: ChangeEvent<HTMLSelectElement>) => onFilterChange({ sort: event.target.value, offset: 0 });
  const changeAdmin = (event: ChangeEvent<HTMLSelectElement>) => onFilterChange({ admin: event.target.value || undefined, offset: 0 });

  return (
    <Stack dir={i18n.dir()} spacing={3.5} px={{ base: 3, md: 4 }} pt={4} pb={3.5}>
      <HStack justify="space-between" align="center" gap={3} flexWrap="wrap">
        <HStack spacing={2} flexWrap="wrap">
          {accountActive && account.data?.billing_mode !== "USER_CREDIT" && ["FREE_FORM", "FORM_ONLY", "BOTH"].includes(account.data?.user_creation_mode || "") && (
            <Button size="sm" colorScheme="primary" color="var(--panel-accent-contrast)" leftIcon={<AddIcon />} onClick={() => onCreateUser(true)}>
              افزودن کاربر
            </Button>
          )}
          {accountActive && (account.data?.billing_mode === "USER_CREDIT" || ["PLAN_ONLY", "BOTH"].includes(account.data?.user_creation_mode || "")) && (
            <Button size="sm" colorScheme="primary" color="var(--panel-accent-contrast)" leftIcon={<AddIcon />} onClick={() => setPlanCreateOpen(true)}>
              ساخت از پلن
            </Button>
          )}
          <Tooltip label="به‌روزرسانی کاربران">
            <IconButton aria-label="به‌روزرسانی کاربران" icon={loading ? <Spinner size="xs" /> : <ReloadIcon />} size="sm" variant="outline" borderColor="var(--panel-border)" onClick={refetchUsers} isDisabled={loading} />
          </Tooltip>
        </HStack>

        <HStack
          spacing={1}
          p={1}
          bg="var(--panel-nested)"
          borderWidth="1px"
          borderColor="var(--panel-border)"
          borderRadius="14px"
          overflowX="auto"
          maxW="full"
        >
          <StatusSegment active={!filters.status} label="همه" onClick={() => setStatus(undefined)} />
          <StatusSegment active={filters.status === "active"} label="فعال" onClick={() => setStatus("active")} />
          <StatusSegment active={filters.status === "disabled"} label="غیرفعال" onClick={() => setStatus("disabled")} />
          <StatusSegment active={filters.status === "expired"} label="منقضی" onClick={() => setStatus("expired")} />
          <StatusSegment active={filters.status === "on_hold"} label="در انتظار" onClick={() => setStatus("on_hold")} />
        </HStack>

        <HStack w={{ base: "full", lg: "360px" }} flexShrink={0} spacing={2}>
          <InputGroup flex="1">
            <InputLeftElement pointerEvents="none" h="42px" color="var(--panel-text-muted)"><SearchIcon /></InputLeftElement>
            <Input
              h="42px"
              value={search}
              onChange={(event) => {
                setSearch(event.target.value);
                updateSearch(event.target.value.trim());
              }}
              placeholder="جستجوی کاربر..."
              fontSize="12px"
              {...control}
            />
          </InputGroup>
          <Tooltip label="فیلتر پیشرفته">
            <IconButton
              aria-label="فیلتر پیشرفته"
              aria-expanded={advancedOpen}
              icon={<AdvancedIcon />}
              h="42px"
              minW="42px"
              variant={advancedOpen ? "solid" : "outline"}
              color={advancedOpen ? "var(--panel-accent-contrast)" : "var(--panel-text-body)"}
              bg={advancedOpen ? "var(--panel-accent)" : "var(--panel-surface)"}
              borderColor={advancedOpen ? "var(--panel-accent)" : "var(--panel-border)"}
              onClick={() => setAdvancedOpen((value) => !value)}
              _hover={{ bg: advancedOpen ? "var(--panel-accent-hover)" : "var(--panel-row-hover)" }}
            />
          </Tooltip>
        </HStack>
      </HStack>

      <Collapse in={advancedOpen} animateOpacity>
        <Box pt={3} borderTopWidth="1px" borderColor="var(--panel-border)">
          <HStack justify="space-between" align="center" gap={3} flexWrap="wrap">
            <Text color="var(--panel-text-muted)" fontSize="11px">فیلترهای تکمیلی</Text>
            <HStack spacing={2} flexWrap="wrap">
              {canManageAdmins && (
                <Select aria-label="فیلتر ادمین" value={filters.admin || ""} onChange={changeAdmin} size="sm" w={{ base: "160px", md: "190px" }} {...control}>
                  <option value="">همه ادمین‌ها</option>
                  {adminOptions.data?.map((admin) => <option key={admin.username} value={admin.username}>{admin.username}</option>)}
                </Select>
              )}
              <Select aria-label="مرتب‌سازی کاربران" value={filters.sort} onChange={changeSort} size="sm" w={{ base: "180px", md: "210px" }} {...control}>
                <option value="-created_at">جدیدترین‌ها</option>
                <option value="created_at">قدیمی‌ترین‌ها</option>
                <option value="username">نام کاربری A-Z</option>
                <option value="-username">نام کاربری Z-A</option>
                <option value="-used_traffic">مصرف بیشتر</option>
                <option value="used_traffic">مصرف کمتر</option>
                <option value="expire">انقضای نزدیک</option>
                <option value="-expire">انقضای دور</option>
              </Select>
            </HStack>
          </HStack>
        </Box>
      </Collapse>

      <CreateUserFromPlan isOpen={planCreateOpen} onClose={() => setPlanCreateOpen(false)} />
    </Stack>
  );
};

export default FiltersCompact;
''')

# ---------------------------------------------------------------------------
# Users table: soft status badges, thin traffic progress, reduced action clutter.
# ---------------------------------------------------------------------------
users_path = "app/dashboard/src/components/UsersTablePro.tsx"
users = read(users_path)
users = users.replace("  CircularProgress,\n  CircularProgressLabel,\n", "  Menu,\n  MenuButton,\n  MenuDivider,\n  MenuItem,\n  MenuList,\n  Progress,\n")
users = users.replace("  DocumentMagnifyingGlassIcon,\n", "  DocumentMagnifyingGlassIcon,\n  EllipsisVerticalIcon,\n")
users = users.replace("const AuditIcon = chakra(DocumentMagnifyingGlassIcon, { baseStyle: { w: 4, h: 4 } });", "const AuditIcon = chakra(DocumentMagnifyingGlassIcon, { baseStyle: { w: 4, h: 4 } });\nconst MoreIcon = chakra(EllipsisVerticalIcon, { baseStyle: { w: 4, h: 4 } });")
old_status = re.search(r'const statusMeta: Record<User\["status"\],.*?\n\};', users, flags=re.S)
if not old_status:
    raise RuntimeError("Users statusMeta not found")
users = users[:old_status.start()] + r'''const statusMeta: Record<User["status"], { label: string; color: string; bg: string; border: string; dot: string }> = {
  active: { label: "فعال", color: "var(--panel-success)", bg: "var(--panel-success-soft)", border: "var(--panel-success-border)", dot: "var(--panel-success)" },
  connected: { label: "فعال", color: "var(--panel-success)", bg: "var(--panel-success-soft)", border: "var(--panel-success-border)", dot: "var(--panel-success)" },
  connecting: { label: "در اتصال", color: "var(--panel-info)", bg: "var(--panel-info-soft)", border: "var(--panel-info-border)", dot: "var(--panel-info)" },
  on_hold: { label: "در انتظار", color: "var(--panel-warning)", bg: "var(--panel-warning-soft)", border: "var(--panel-warning-border)", dot: "var(--panel-warning)" },
  disabled: { label: "غیرفعال", color: "var(--panel-text-muted)", bg: "var(--panel-muted-soft)", border: "var(--panel-border-strong)", dot: "var(--panel-text-muted)" },
  expired: { label: "منقضی", color: "var(--panel-danger)", bg: "var(--panel-danger-soft)", border: "var(--panel-danger-border)", dot: "var(--panel-danger)" },
  limited: { label: "محدود", color: "var(--panel-warning)", bg: "var(--panel-warning-soft)", border: "var(--panel-warning-border)", dot: "var(--panel-warning)" },
  error: { label: "خطا", color: "var(--panel-danger)", bg: "var(--panel-danger-soft)", border: "var(--panel-danger-border)", dot: "var(--panel-danger)" },
};''' + users[old_status.end():]

usage_start = users.index('const UsageCell: FC<{ user: User }>')
status_pill_start = users.index('const StatusPill:', usage_start)
users = users[:usage_start] + r'''const UsageCell: FC<{ user: User }> = ({ user }) => {
  const used = user.used_traffic ?? 0;
  const unlimited = !user.data_limit;
  const percent = unlimited ? 0 : Math.min(100, Math.max(0, (used / Math.max(user.data_limit || 1, 1)) * 100));
  const color = percent >= 90 ? "var(--panel-danger)" : percent >= 70 ? "var(--panel-warning)" : "var(--panel-success)";
  return (
    <Stack spacing={1.5} minW={0} w="full">
      <HStack justify="space-between" spacing={2} minW={0}>
        <Text dir="ltr" textAlign="start" fontSize="10px" fontWeight="800" noOfLines={1} sx={{ unicodeBidi: "isolate" }}>
          {String(formatBytes(used))} / {user.data_limit ? String(formatBytes(user.data_limit)) : "∞"}
        </Text>
        {unlimited ? (
          <Box px={2} py={0.5} borderWidth="1px" borderColor="var(--panel-accent-border)" borderRadius="full" color="var(--panel-accent)" fontSize="11px" fontWeight="900">∞</Box>
        ) : (
          <Text color="var(--panel-text-muted)" fontSize="9px">{Math.round(percent)}٪</Text>
        )}
      </HStack>
      {!unlimited && <Progress value={percent} h="4px" borderRadius="full" bg="var(--panel-nested)" sx={{ "& > div": { background: color } }} />}
      <Text color="var(--panel-text-muted)" fontSize="9px">مصرف داده</Text>
    </Stack>
  );
};

''' + users[status_pill_start:]

status_start = users.index('const StatusPill:')
action_start = users.index('const Action:', status_start)
users = users[:status_start] + r'''const StatusPill: FC<{ status: User["status"] }> = ({ status }) => {
  const meta = statusMeta[status];
  return (
    <HStack w="fit-content" spacing={1.5} px={2.5} py={1.25} borderRadius="full" bg={meta.bg} borderWidth="1px" borderColor={meta.border}>
      <Box boxSize="6px" borderRadius="full" bg={meta.dot} />
      <Text color={meta.color} fontSize="10px" fontWeight="750">{meta.label}</Text>
    </HStack>
  );
};

''' + users[action_start:]
users = users.replace('borderRadius="7px"', 'borderRadius="12px"')
users = users.replace('minW="28px"\n        w="28px"\n        h="28px"', 'minW="32px"\n        w="32px"\n        h="32px"')

old_table = '<TableContainer overflowX="hidden" borderWidth="1px" borderColor="var(--panel-border)" borderRadius="10px">\n        <Table size="sm" w="full" sx={{ tableLayout: "fixed", "th, td": { borderColor: "var(--panel-border)", px: 2, py: 2, overflow: "hidden" }, "th": { whiteSpace: "normal", lineHeight: 1.3 } }}>'
new_table = '<TableContainer overflowX="hidden" borderWidth="1px" borderColor="var(--panel-border)" borderRadius="16px" bg="var(--panel-surface)" boxShadow="var(--shadow-panel)">\n        <Table size="sm" w="full" sx={{ tableLayout: "fixed", "th, td": { borderBottom: "0 !important", px: 3.5, py: 3, overflow: "hidden" }, "th": { whiteSpace: "normal", lineHeight: 1.45, fontWeight: 600, color: "var(--panel-text-muted)" } }}>'
users = replace_once(users, old_table, new_table, "Users table shell")

old_tr = '''                <Tr
                  key={user.username}
                  bg={selectedMap.has(user.username) ? "var(--panel-accent-soft)" : "transparent"}
                  transition="background .14s ease"
                  _hover={{ bg: selectedMap.has(user.username) ? "var(--panel-accent-soft-strong)" : "var(--panel-row-hover)" }}
                >'''
new_tr = '''                <Tr
                  key={user.username}
                  data-selected={selectedMap.has(user.username) ? "true" : undefined}
                  data-disabled={user.status === "disabled" ? "true" : undefined}
                  transition="opacity .14s ease"
                >'''
users = replace_once(users, old_tr, new_tr, "Users row styling")

old_actions = re.search(r'''                    <HStack justify="end" gap=\{1\} rowGap=\{1\} dir="ltr" flexWrap="wrap" maxW="full">.*?                    </HStack>''', users, flags=re.S)
if not old_actions:
    raise RuntimeError("Users action cluster not found")
new_actions = r'''                    <HStack justify="end" gap={1.5} dir="ltr" maxW="full">
                      <Action label="کپی لینک اشتراک" icon={<CopyIcon />} onClick={() => copySubscription(user)} tone="green" />
                      {!readOnly && <Action label="ویرایش" icon={<EditIcon />} onClick={() => onEditingUser(user)} tone="blue" disabled={busy} />}
                      {!readOnly && <Action label="حذف کاربر" icon={<DeleteIcon />} onClick={() => onDeletingUser(user)} tone="red" disabled={busy} />}
                      <Menu placement="bottom-end" isLazy>
                        <MenuButton
                          as={IconButton}
                          aria-label="عملیات بیشتر"
                          icon={<MoreIcon />}
                          size="xs"
                          minW="32px"
                          w="32px"
                          h="32px"
                          borderRadius="12px"
                          color="var(--panel-text-body)"
                          bg="var(--panel-nested)"
                          borderWidth="1px"
                          borderColor="var(--panel-border)"
                          _hover={{ bg: "var(--panel-row-hover)" }}
                        />
                        <MenuList dir="rtl" minW="210px" bg="var(--panel-surface)" borderColor="var(--panel-border)" borderRadius="14px" boxShadow="var(--shadow-elevated)" py={1.5}>
                          <MenuItem icon={<QRIcon />} onClick={() => { setQRCode(user.links); setSubLink(user.subscription_url); }}>QR Code</MenuItem>
                          <MenuItem icon={<AuditIcon />} onClick={() => navigate(`/audit-logs/?search=${encodeURIComponent(user.username)}`)}>گزارش فعالیت</MenuItem>
                          {!readOnly && <MenuDivider borderColor="var(--panel-border)" />}
                          {!readOnly && <MenuItem icon={<RenewIcon />} isDisabled={busy} onClick={() => { renewalRequest.current = null; setRenewalUser(user); setRenewalPlanId(""); renewalModal.onOpen(); }}>تمدید با پلن</MenuItem>}
                          {!readOnly && <MenuItem icon={user.status === "disabled" ? <PlayActionIcon /> : <PauseActionIcon />} isDisabled={busy} onClick={() => toggleStatus(user)}>{user.status === "disabled" ? "فعال‌سازی" : "غیرفعال‌سازی"}</MenuItem>}
                          {!readOnly && <MenuItem icon={<ResetIcon />} isDisabled={busy} onClick={() => resetUsage(user)}>بازنشانی مصرف</MenuItem>}
                          {!readOnly && <MenuItem icon={<RevokeIcon />} isDisabled={busy} onClick={() => revoke(user)}>ابطال لینک اشتراک</MenuItem>}
                        </MenuList>
                      </Menu>
                    </HStack>'''
users = users[:old_actions.start()] + new_actions + users[old_actions.end():]
users = users.replace('bg="#0c1524" color="gray.100" borderWidth="1px" borderColor="rgba(148,163,184,.16)" borderRadius="14px"', 'bg="var(--panel-surface)" color="var(--panel-text)" borderWidth="1px" borderColor="var(--panel-border)" borderRadius="16px"')
users = users.replace('color="gray.900" isDisabled={!renewalUser || !renewalPlanId}', 'color="var(--panel-accent-contrast)" isDisabled={!renewalUser || !renewalPlanId}')
write(users_path, users)

# ---------------------------------------------------------------------------
# Admin UI: preserve current modular UI (newer than the old branch), fold in the
# useful minimal-pro styling without regressing hierarchy/billing features.
# ---------------------------------------------------------------------------
admin_ui_path = "app/dashboard/src/pages/admins/AdminUi.tsx"
admin_ui = read(admin_ui_path)
admin_ui = re.sub(r'export const panel = \{.*?\};', 'export const panel = {\n  bg: "var(--panel-surface)",\n  borderColor: "var(--panel-border)",\n};', admin_ui, count=1, flags=re.S)
admin_ui = re.sub(r'export const control = \{.*?\};', 'export const control = {\n  bg: "var(--panel-surface)",\n  borderColor: "var(--panel-border)",\n  _hover: { borderColor: "var(--panel-border-strong)" },\n  _focusVisible: { borderColor: "var(--panel-accent)", boxShadow: "0 0 0 2px var(--panel-accent-soft)" },\n};', admin_ui, count=1, flags=re.S)
admin_ui = re.sub(r'const statusMeta = \{.*?\} as const;', r'''const statusMeta = {
  ACTIVE: { label: "فعال", dot: "var(--panel-success)", text: "var(--panel-success)", bg: "var(--panel-success-soft)", border: "var(--panel-success-border)" },
  SUSPENDED: { label: "فریز", dot: "var(--panel-warning)", text: "var(--panel-warning)", bg: "var(--panel-warning-soft)", border: "var(--panel-warning-border)" },
  DISABLED: { label: "غیرفعال", dot: "var(--panel-text-muted)", text: "var(--panel-text-muted)", bg: "var(--panel-muted-soft)", border: "var(--panel-border-strong)" },
} as const;''', admin_ui, count=1, flags=re.S)
admin_ui = admin_ui.replace('borderRadius="14px"', 'borderRadius="16px"')
admin_ui = admin_ui.replace('borderRadius="11px"', 'borderRadius="12px"')
admin_ui = admin_ui.replace('<HStack w="fit-content" spacing={1.5} px={2.5} py={1.5} bg={meta.bg} borderRadius="full">', '<HStack w="fit-content" spacing={1.5} px={2.5} py={1.25} bg={meta.bg} borderWidth="1px" borderColor={meta.border} borderRadius="full">')
admin_ui = admin_ui.replace('borderRadius="8px"', 'borderRadius="12px"')
admin_ui = admin_ui.replace('borderRadius="7px"', 'borderRadius="12px"')
admin_ui = admin_ui.replace('bg={active ? "rgba(37,99,235,.18)" : "transparent"}', 'bg={active ? "var(--panel-accent-soft)" : "transparent"}')
admin_ui = admin_ui.replace('borderColor={active ? "rgba(96,165,250,.55)" : "rgba(148,163,184,.18)"}', 'borderColor={active ? "var(--panel-accent-border)" : "var(--panel-border)"}')
admin_ui = admin_ui.replace('color={active ? "blue.100" : "gray.300"}', 'color={active ? "var(--panel-accent)" : "var(--panel-text-body)"}')
admin_ui = admin_ui.replace('bg: active ? "rgba(37,99,235,.24)" : "whiteAlpha.100"', 'bg: active ? "var(--panel-accent-soft-strong)" : "var(--panel-row-hover)"')
write(admin_ui_path, admin_ui)

admin_table_path = "app/dashboard/src/pages/admins/AdminTable.tsx"
admin_table = read(admin_table_path)
admin_table = admin_table.replace('borderRadius="9px"', 'borderRadius="12px"')
admin_table = admin_table.replace('<Thead bg="rgba(2,8,23,.38)">', '<Thead bg="var(--panel-nested)">')
admin_table = admin_table.replace('_hover={{ bg: "rgba(255,255,255,.028)", boxShadow: "inset 3px 0 0 rgba(59,130,246,.55)" }}', '_hover={{ bg: "var(--panel-row-hover)", boxShadow: "inset 3px 0 0 var(--panel-accent)" }}')
admin_table = admin_table.replace('<Tr\n                    role="group"', '<Tr\n                    role="group"\n                    data-disabled={item.account_status === "DISABLED" ? "true" : undefined}')
write(admin_table_path, admin_table)

# ---------------------------------------------------------------------------
# Access Group moves from Settings into Plans. No option is removed.
# Settings remains as Configuration for pricing/backup/branding.
# ---------------------------------------------------------------------------
settings_path = "app/dashboard/src/pages/Settings.tsx"
settings = read(settings_path)
settings = settings.replace('import { AccessGroupManager } from "components/AccessGroupManager";\n', '')
settings = settings.replace('  { id: "access-groups", title: "گروه‌های دسترسی", caption: "شبکه و دسترسی کاربر" },\n', '')
settings = settings.replace('              تنظیمات مالک پنل', '              پیکربندی مالک پنل')
settings = settings.replace('<Heading size="lg">تنظیمات</Heading>', '<Heading size="lg">پیکربندی</Heading>')
settings, removed = re.subn(r'''\n            <Section\n              id="access-groups".*?\n            </Section>\n''', '\n', settings, count=1, flags=re.S)
if removed != 1:
    raise RuntimeError("Access Group Settings section not found")
write(settings_path, settings)

plans_path = "app/dashboard/src/pages/Plans.tsx"
plans = read(plans_path)
if 'import { AccessGroupManager } from "components/AccessGroupManager";' not in plans:
    plans = plans.replace('import { AppShell } from "components/AppShell";\n', 'import { AccessGroupManager } from "components/AccessGroupManager";\nimport { AppShell } from "components/AppShell";\n')
plans = plans.replace('color="#07130e"', 'color="var(--panel-accent-contrast)"')
plans = plans.replace('bg="#111d17" color="gray.100" borderWidth="1px" borderColor="#33483b" borderRadius="18px"', 'bg="var(--panel-surface)" color="var(--panel-text)" borderWidth="1px" borderColor="var(--panel-border)" borderRadius="16px"')
plans = plans.replace('bg="#111d17" borderWidth="1px" borderColor="#33483b"', 'bg="var(--panel-surface)" borderWidth="1px" borderColor="var(--panel-border)"')
insert_anchor = '      {!plans.isLoading && !plans.isError && (plans.data || []).length === 0 && <Card p={8}'
insert_at = plans.index(insert_anchor)
access_section = r'''      {account.data?.role === "OWNER" && (
        <Card mt={6} p={{ base: 4, md: 5 }} bg="var(--panel-surface)" borderWidth="1px" borderColor="var(--panel-border)" borderRadius="16px">
          <Stack spacing={1} mb={5}>
            <Text color="var(--panel-accent)" fontSize="xs" fontWeight="800">دسترسی شبکه</Text>
            <Text as="h2" fontSize="xl" fontWeight="800">Access Groups</Text>
            <Text color="var(--panel-text-muted)" fontSize="sm">گروه دسترسی، Node / Inbound / Host و ادمین‌های مجاز را مشخص می‌کند و از شرایط تجاری پلن مستقل می‌ماند.</Text>
          </Stack>
          <AccessGroupManager />
        </Card>
      )}

'''
plans = plans[:insert_at] + access_section + plans[insert_at:]
write(plans_path, plans)

print("v1.0.6 UI integration patch applied")
