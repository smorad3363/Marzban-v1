# Marzban Console design system

Reviewed direction, 2026-11-06. This is a frontend presentation release based on v1.1.21 (`270ffdd`). All eight routes, role guards, panel options, API calls and commercial behavior remain the baseline contract.

## Visual direction

Restrained glass, quiet hierarchy, high information density. White and near-black surfaces with a muted jade accent. Glass is reserved for the sidebar and transient overlays; table rows and content cards use solid backgrounds. No animated blur, decorative particles, large background images or remote font services.

The UI/UX search recommended minimal enterprise styling and tabular typography. Its marketing page patterns, React 19 compiler suggestions, SaaS display fonts and dark-only IoT palette were rejected: this application is a React 18 Persian operations console. The verified choices below replace those generated suggestions.

| Token | White theme | Black theme |
| --- | --- | --- |
| Background | `#f4f6f3` | `#0b100e` |
| Surface | `#ffffff` | `#141b18` |
| Text | `#18251e` | `#edf3ee` |
| Body | `#354b3f` | `#c1cfc5` |
| Muted | `#5c6f62` | `#a1b0a6` |
| Accent | `#0b7560` | `#65d6bd` |
| On accent | `#ffffff` | `#08251c` |
| Border | `#e0e7e1` | `#2a372f` |
| Control border | `#7f9386` | `#5c7063` |

Source of truth: `src/index.scss` semantic `--panel-*` variables. Chakra definitions live in `chakra.config.ts`. Do not append a second palette or page-specific dark overrides.

## Composition

- `PageHeader`: one h1, optional eyebrow, description and existing actions. Never put entire page headers in decorative hero cards.
- `Surface`, `Metric`, `SectionHeader`, `EmptyState`, `TechnicalValue`: shared presentation primitives in `src/design-system/Console.tsx`, independent of APIs and account policy.
- Main workspace: maximum 1680px, sidebar 248px, 16px mobile and 28–36px desktop content inset.
- Spacing: 4 / 8 / 12 / 16 / 20 / 24 / 32. Panels 18px radius, controls 10px, badges 6px. Use one quiet elevation level and one overlay shadow.
- Font: local variable Vazirmatn for Persian, local variable Inter for Latin; system monospace for technical data. 14px body, 12px metadata, 26–32px page titles; 16px form inputs on coarse pointers. Avoid extra-bold walls of text.
- Charts use `useChartPalette()` so axes, labels, tooltips and data colors adapt together. No chart entrance animation or animated polling values.

## Interaction and accessibility

- Retain Chakra's dialog focus trap, Escape behavior, initial focus, focus return and existing pending-submit guards.
- Minimum touch targets 44px on coarse pointers; stable 40–44px controls on desktop. Keyboard focus is a 2px jade outline with 3px offset. A skip link leads to main content.
- RTL uses logical margins and padding. IPs, UUIDs, paths and subscription links are isolated LTR; surrounding Persian text retains RTL.
- Menus must remain inside the viewport. Long labels wrap; identity and financial values must not push page width.
- Dense tables retain horizontal scrolling inside their containers, never on the page. Mobile layouts prioritize identity, status and current usage with all actions reachable.
- Motion: short color feedback at 140ms; occasional overlays at 180–240ms with an ease-out curve. No hover lift for data rows, no continuous status pulse, no animated backdrop blur. Respect `prefers-reduced-motion` and hover-capable pointers.
- Two themes are preference-persistent through the existing color-mode mechanism. No third theme or new product setting.

## Verification boundaries

`node scripts/test-ui-boundaries.cjs` compares all original request/query definitions, action handlers, disabled/hidden guards and select options to the recorded baseline. Service, contexts, hooks, types, backend, installer, VERSION and accounting files must not change.

`preview/server.cjs` serves the exact production bundle against synthetic fixtures. It has no database, production API proxy or real credentials. Its visible review controls cover five role profiles and demo/worst/empty/one/huge/loading/error states. These controls are injected by the preview server and are absent from the production build.

Test responsive widths 320, 375, 768, 1024 and 1440, both themes, long Persian and Latin values, large and negative financial values, empty lists, loading/errors, disabled accounts, keyboard navigation, reduced motion and dialog submission. Physical phone testing must be reported separately from browser viewport tests.
