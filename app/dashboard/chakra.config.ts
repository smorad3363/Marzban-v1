import { extendTheme } from "@chakra-ui/react";

const field = {
  bg: "var(--panel-input)", color: "var(--panel-text)", borderColor: "var(--panel-border-strong)",
  borderRadius: "var(--radius-control)", transition: "border-color 140ms ease, box-shadow 140ms ease",
  _placeholder: { color: "var(--panel-text-muted)", opacity: 1 },
  _hover: { borderColor: "var(--panel-accent-border)" },
  _focusVisible: { borderColor: "var(--panel-accent)", boxShadow: "0 0 0 3px var(--panel-accent-soft)" },
  _invalid: { borderColor: "var(--panel-danger)", boxShadow: "none" },
  _disabled: { opacity: .55, cursor: "not-allowed" },
};
const dialog = {
  bg: "var(--panel-surface)", color: "var(--panel-text)", border: "1px solid var(--panel-border-strong)",
  borderRadius: "var(--radius-panel)", boxShadow: "var(--shadow-elevated)",
};
const closeButton = {
  top: 3, insetInlineEnd: 3, insetInlineStart: "auto", zIndex: 30, pointerEvents: "auto", w: "40px", h: "40px",
  color: "var(--panel-text-body)", bg: "var(--panel-nested)", borderRadius: "10px",
  _hover: { bg: "var(--panel-row-hover)" },
};
const semanticTone = (scheme: string): string | undefined => (({ primary: "accent", green: "success", red: "danger", orange: "warning", yellow: "warning", blue: "info", cyan: "info" } as Record<string, string>)[scheme]);
const solidButton = (p: any) => {
  const tone = semanticTone(p.colorScheme);
  if (!tone) return { bg: "var(--panel-nested)", color: "var(--panel-text)", _hover: { bg: "var(--panel-row-hover)" } };
  const bg = `var(--panel-${tone})`;
  return { bg, color: "var(--panel-accent-contrast)", boxShadow: "0 1px 2px rgb(0 0 0 / .08)", _hover: { bg: tone === "accent" ? "var(--panel-accent-hover)" : bg, boxShadow: `0 0 0 3px var(--panel-${tone}-soft)`, _disabled: { bg, boxShadow: "none" } }, _active: { bg, transform: "translateY(1px)" } };
};
const outlineButton = (p: any) => {
  const tone = semanticTone(p.colorScheme);
  return { bg: "transparent", borderColor: tone ? `var(--panel-${tone}-border)` : "var(--panel-border-strong)", color: tone ? `var(--panel-${tone})` : "var(--panel-text-body)", _hover: { bg: tone ? `var(--panel-${tone}-soft)` : "var(--panel-row-hover)", borderColor: tone ? `var(--panel-${tone})` : "var(--panel-accent-border)" }, _active: { bg: "var(--panel-muted-soft)" } };
};
const badgeVariant = (variant: "solid" | "subtle" | "outline") => (p: any) => {
  const tone = semanticTone(p.colorScheme);
  return { bg: variant === "outline" ? "transparent" : tone ? `var(--panel-${tone}${variant === "subtle" ? "-soft" : ""})` : "var(--panel-muted-soft)", color: tone ? variant === "solid" ? "var(--panel-accent-contrast)" : `var(--panel-${tone})` : "var(--panel-text-body)", borderWidth: "1px", borderColor: tone ? `var(--panel-${tone}-border)` : "var(--panel-border)" };
};
export const theme = extendTheme({
  config: { initialColorMode: "dark", useSystemColorMode: false },
  fonts: { heading: "Inter, Vazirmatn, sans-serif", body: "Inter, Vazirmatn, sans-serif", mono: "ui-monospace, SFMono-Regular, Consolas, monospace" },
  colors: { primary: { 50: "#eaf7f2", 100: "#ccede1", 200: "#a3e1ce", 300: "#82d9c2", 400: "#65d6bd", 500: "#0e9277", 600: "#0b7560", 700: "#095e4e", 800: "#064c40", 900: "#063c32" } },
  shadows: { outline: "0 0 0 3px var(--panel-accent-soft)", panel: "var(--shadow-panel)", elevated: "var(--shadow-elevated)" },
  radii: { md: "10px", lg: "12px", xl: "16px", '2xl': "20px" },
  styles: { global: {
    body: { bg: "var(--panel-bg)", color: "var(--panel-text)", lineHeight: 1.75, overflowWrap: "anywhere" },
    'html[lang^="fa"]': { "--chakra-fonts-heading": "Vazirmatn, Inter, sans-serif", "--chakra-fonts-body": "Vazirmatn, Inter, sans-serif" },
    "::selection": { bg: "var(--panel-accent-soft-strong)", color: "var(--panel-text)" },
  } },
  components: {
    Button: {
      baseStyle: { borderRadius: "var(--radius-control)", fontWeight: "600", lineHeight: 1.6, whiteSpace: "normal", flexShrink: 0, gap: 1, transition: "background-color 140ms ease, color 140ms ease, border-color 140ms ease, box-shadow 140ms ease", _disabled: { opacity: .45, cursor: "not-allowed", boxShadow: "none" } },
      sizes: { xs: { minH: "32px", h: "auto", py: 1, px: 2.5, fontSize: "xs" }, sm: { minH: "40px", h: "auto", py: 2, px: 3.5, fontSize: "sm" }, md: { minH: "44px", h: "auto", py: 2.5, px: 4, fontSize: "sm" }, lg: { minH: "48px", h: "auto", py: 3, px: 5, fontSize: "md" } },
      variants: {
        solid: solidButton,
        outline: outlineButton,
        ghost: { color: "var(--panel-text-body)", _hover: { bg: "var(--panel-muted-soft)" }, _active: { bg: "var(--panel-row-hover)" } },
      },
    },
    Card: { baseStyle: { container: { ...dialog, borderColor: "var(--panel-border)", borderRadius: "var(--radius-panel)", boxShadow: "var(--shadow-panel)", minW: 0 } } },
    Modal: { baseStyle: { dialog, overlay: { bg: "var(--panel-overlay)", backdropFilter: "blur(5px)" }, header: { fontSize: "lg", fontWeight: 700, paddingInlineEnd: 16, borderBottom: "1px solid var(--panel-border)", py: 5, flexShrink: 0 }, body: { py: 5, minH: 0, overscrollBehavior: "contain" }, footer: { borderTop: "1px solid var(--panel-border)", gap: 2, py: 4, flexWrap: "wrap", flexShrink: 0 }, closeButton } },
    Drawer: { baseStyle: { dialog, overlay: { bg: "var(--panel-overlay)" }, header: { fontSize: "lg", paddingInlineEnd: 16, borderBottom: "1px solid var(--panel-border)", py: 5 }, body: { py: 5 }, footer: { borderTop: "1px solid var(--panel-border)", gap: 2, py: 4 }, closeButton } },
    Input: { variants: { outline: { field } }, sizes: { sm: { field: { minH: "40px", fontSize: "sm", px: 3 } }, md: { field: { minH: "44px", fontSize: "sm", px: 3.5 } } } },
    NumberInput: { variants: { outline: { field } }, baseStyle: { stepper: { borderColor: "var(--panel-border)", color: "var(--panel-text-muted)" } } },
    Select: { variants: { outline: { field } }, sizes: { sm: { field: { minH: "40px", fontSize: "sm", px: 3, paddingInlineEnd: 9 } }, md: { field: { minH: "44px", fontSize: "sm", px: 3.5, paddingInlineEnd: 9 } } } },
    Textarea: { variants: { outline: { ...field, lineHeight: 1.9, py: 3 } } },
    FormLabel: { baseStyle: { fontSize: "sm", fontWeight: 500, mb: 2, lineHeight: 1.8, whiteSpace: "normal", overflowWrap: "anywhere", color: "var(--panel-text-body)" } },
    Form: { baseStyle: { helperText: { fontSize: "xs", lineHeight: 1.9, color: "var(--panel-text-muted)" } } },
    Alert: { baseStyle: { container: { borderRadius: "12px", fontSize: "sm", lineHeight: 1.9, borderWidth: "1px" } } },
    Badge: { variants: { solid: badgeVariant("solid"), subtle: badgeVariant("subtle"), outline: badgeVariant("outline") }, baseStyle: { borderRadius: "6px", textTransform: "none", fontWeight: 600, px: 2, py: .5, whiteSpace: "normal", lineHeight: 1.8 } },
    Menu: { baseStyle: { list: { ...dialog, borderRadius: "14px", p: 1.5, minW: "210px" }, item: { bg: "transparent", borderRadius: "8px", py: 2.5, fontSize: "sm", _focus: { bg: "var(--panel-accent-soft)" }, _active: { bg: "var(--panel-accent-soft-strong)" } } } },
    Popover: { baseStyle: { content: { ...dialog, borderRadius: "14px" }, header: { borderColor: "var(--panel-border)" }, footer: { borderColor: "var(--panel-border)" } } },
    Tooltip: { baseStyle: { bg: "var(--panel-text)", color: "var(--panel-bg)", borderRadius: "8px", px: 3, py: 2, fontSize: "xs", boxShadow: "var(--shadow-panel)" } },
    Tabs: { baseStyle: { tab: { fontWeight: 600, py: 3, fontSize: "sm", color: "var(--panel-text-muted)", _selected: { color: "var(--panel-accent)", borderColor: "var(--panel-accent)" } }, tablist: { borderColor: "var(--panel-border)" }, tabpanel: { px: 0, py: 5 } } },
    Table: { baseStyle: { table: { borderCollapse: "separate", borderSpacing: 0, fontVariantNumeric: "tabular-nums" }, thead: { bg: "var(--panel-nested)" }, th: { bg: "var(--panel-nested)", color: "var(--panel-text-muted)", fontSize: "xs", fontWeight: 500, letterSpacing: 0, textTransform: "none", px: 3, py: 2.5, borderBottom: "1px solid var(--panel-border)", whiteSpace: "nowrap" }, td: { px: 3, py: 3, color: "var(--panel-text-body)", borderBottom: "1px solid var(--panel-border)", lineHeight: 1.8, transition: "background-color 120ms ease" } } },
    Skeleton: { baseStyle: { startColor: "var(--panel-nested)", endColor: "var(--panel-border)", borderRadius: "10px" } },
    Divider: { baseStyle: { borderColor: "var(--panel-border)", opacity: 1 } },
    Code: { baseStyle: { bg: "var(--panel-nested)", color: "var(--panel-text-body)", borderRadius: "8px", px: 2, py: 1, fontSize: "xs" } },
    Progress: { baseStyle: { track: { bg: "var(--panel-nested)", borderRadius: "full" }, filledTrack: { borderRadius: "full" } } },
  },
});
