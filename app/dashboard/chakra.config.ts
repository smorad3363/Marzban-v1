import { extendTheme } from "@chakra-ui/react";

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
