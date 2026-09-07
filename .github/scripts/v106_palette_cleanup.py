from pathlib import Path

src = Path("app/dashboard/src")

# Normalize fixed gray foreground tokens so the same source works in both modes.
foreground = {
    'color="gray.100"': 'color="var(--panel-text)"',
    'color="gray.200"': 'color="var(--panel-text-body)"',
    'color="gray.300"': 'color="var(--panel-text-body)"',
    'color="gray.400"': 'color="var(--panel-text-muted)"',
    'color="gray.500"': 'color="var(--panel-text-muted)"',
    'color="gray.600"': 'color="var(--panel-text-muted)"',
    'color="gray.700"': 'color="var(--panel-text-body)"',
    'color="gray.800"': 'color="var(--panel-text-body)"',
    'color="gray.900"': 'color="var(--panel-text)"',
}
for path in src.rglob("*.tsx"):
    text = path.read_text(encoding="utf-8")
    for old, new in foreground.items():
        text = text.replace(old, new)
    path.write_text(text, encoding="utf-8")

# Header contains conditional string literals rather than direct color props.
header = src / "components/Header.tsx"
text = header.read_text(encoding="utf-8")
text = text.replace('danger ? "red.200" : "gray.200"', 'danger ? "var(--panel-danger)" : "var(--panel-text-body)"')
text = text.replace('danger ? "red.100" : "white"', 'danger ? "var(--panel-danger)" : "var(--panel-text)"')
text = text.replace('danger ? "rgba(239, 68, 68, .14)" : "whiteAlpha.100"', 'danger ? "var(--panel-danger-soft)" : "var(--panel-row-hover)"')
text = text.replace('danger ? "rgba(239, 68, 68, .2)" : "whiteAlpha.200"', 'danger ? "var(--panel-danger-soft)" : "var(--panel-nested)"')
text = text.replace('"gray.200"', '"var(--panel-text-body)"')
header.write_text(text, encoding="utf-8")

# Replace known pre-v1.0.6 dark/green surfaces with semantic panel tokens.
replacements = {
    'bg="#111d17"': 'bg="var(--panel-surface)"',
    'bg="#0c1524"': 'bg="var(--panel-surface)"',
    'bg="#0c1712"': 'bg="var(--panel-surface)"',
    'bg="#0e1914"': 'bg="var(--panel-surface)"',
    'bg="#101e17"': 'bg="var(--panel-nested)"',
    'bg="#0d1812"': 'bg="var(--panel-nested)"',
    'bg="#0b1710"': 'bg="var(--panel-surface)"',
    'borderColor="#33483b"': 'borderColor="var(--panel-border)"',
    'borderColor="#345346"': 'borderColor="var(--panel-border)"',
    'borderColor="#355546"': 'borderColor="var(--panel-border)"',
    'borderColor="#476858"': 'borderColor="var(--panel-border-strong)"',
    'color="#07130e"': 'color="var(--panel-accent-contrast)"',
    'bg="rgba(2,6,23,.32)"': 'bg="var(--panel-nested)"',
    'bg="rgba(2,6,23,.34)"': 'bg="var(--panel-nested)"',
    'backgroundColor: "#111d17"': 'backgroundColor: "var(--panel-surface)"',
    'color: "#f1f5f2"': 'color: "var(--panel-text)"',
}
for path in src.rglob("*.tsx"):
    text = path.read_text(encoding="utf-8")
    for old, new in replacements.items():
        text = text.replace(old, new)
    text = text.replace('bg="linear-gradient(145deg, rgba(17,29,23,.98), rgba(10,24,27,.96))"', 'bg="var(--panel-surface)"')
    path.write_text(text, encoding="utf-8")

# Plans: primary is an action color; labels and cards use neutral text tokens.
plans = src / "pages/Plans.tsx"
text = plans.read_text(encoding="utf-8")
text = text.replace('color="primary.300"', 'color="var(--panel-accent)"')
text = text.replace('borderRadius="14px"', 'borderRadius="16px"')
plans.write_text(text, encoding="utf-8")

# Access-group rows participate in the same 12/16px radius system.
access = src / "components/AccessGroupManager.tsx"
text = access.read_text(encoding="utf-8").replace('borderRadius="10px"', 'borderRadius="12px"')
access.write_text(text, encoding="utf-8")

# Device Limits: remove remaining old green neutral borders/surfaces.
device = src / "pages/DeviceLimits.tsx"
text = device.read_text(encoding="utf-8")
text = text.replace('"#33483b"', '"var(--panel-border)"')
text = text.replace('bg="#0e1914"', 'bg="var(--panel-surface)"')
text = text.replace('borderColor="#345346"', 'borderColor="var(--panel-border)"')
device.write_text(text, encoding="utf-8")

# User dialog: all structural neutral surfaces come from theme tokens.
dialog = src / "components/UserDialog.tsx"
text = dialog.read_text(encoding="utf-8")
for old, new in {
    '"#33483b"': '"var(--panel-border)"',
    'bg="#0d1812"': 'bg="var(--panel-nested)"',
    'bg="#0b1710"': 'bg="var(--panel-surface)"',
    'backgroundColor: "#111d17"': 'backgroundColor: "var(--panel-surface)"',
    'color: "#f1f5f2"': 'color: "var(--panel-text)"',
}.items():
    text = text.replace(old, new)
dialog.write_text(text, encoding="utf-8")

# Theme meta color should match the actual page background in both modes.
theme_color = src / "utils/themeColor.ts"
text = theme_color.read_text(encoding="utf-8")
text = text.replace('colorMode == "dark" ? "#07130e" : "#f3f6f2"', 'colorMode === "dark" ? "#0B0F19" : "#F8FAFC"')
theme_color.write_text(text, encoding="utf-8")

# Global stylesheet: remove decorative primary usage and old select palette.
scss = src / "index.scss"
text = scss.read_text(encoding="utf-8")
text = text.replace('  --panel-accent: #2563EB;\n  --panel-accent-hover: #1D4ED8;', '  --panel-accent: #2563EB;\n  --panel-accent-hover: #1D4ED8;\n  --chakra-colors-primary-500: #2563EB;\n  --chakra-colors-primary-600: #1D4ED8;')
text = text.replace('  --panel-accent: #3B82F6;\n  --panel-accent-hover: #60A5FA;', '  --panel-accent: #3B82F6;\n  --panel-accent-hover: #60A5FA;\n  --chakra-colors-primary-500: #3B82F6;\n  --chakra-colors-primary-600: #60A5FA;')
text = text.replace('.chakra-ui-dark .chakra-select option {\n  color: #f1f5f2;\n  background: #111d17;\n}', '.chakra-ui-dark .chakra-select option {\n  color: var(--panel-text);\n  background: var(--panel-surface);\n}')
text = text.replace('  background: linear-gradient(120deg, transparent 0 72%, rgba(37, 99, 235, 0.035) 72% 73%, transparent 73%);', '  background: none;')
text = text.replace('  background-image:\n    linear-gradient(rgba(96, 165, 250, 0.08) 1px, transparent 1px),\n    linear-gradient(90deg, rgba(96, 165, 250, 0.08) 1px, transparent 1px);\n  background-size: 32px 32px;', '  background-image: none;')
scss.write_text(text, encoding="utf-8")

# Keep existing API compatibility fields for legacy saved preferences, but no active
# UI consumes dashboard_theme anymore. This avoids a DB/API breaking migration.

# Add permanent UI contracts to the standard release build before compilation.
build = Path(".github/workflows/build.yml")
text = build.read_text(encoding="utf-8")
anchor = '''      - name: Build project\n        working-directory: ./app/dashboard\n        run: VITE_BASE_API=/api/ npm run build --if-present -- --outDir /tmp/marzban-dashboard-build --assetsDir statics\n'''
if anchor not in text:
    raise RuntimeError("build workflow frontend anchor not found")
contracts = '''      - name: Verify dashboard UX contracts\n        working-directory: ./app/dashboard\n        run: |\n          node scripts/test-access-groups.cjs\n          node scripts/test-admin-ux.cjs\n          node scripts/test-v106-ui.cjs\n\n'''
text = text.replace(anchor, contracts + anchor, 1)
build.write_text(text, encoding="utf-8")

print("palette consistency cleanup applied")
