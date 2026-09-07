from pathlib import Path
import re

scss_path = Path("app/dashboard/src/index.scss")
scss = scss_path.read_text(encoding="utf-8")
# Remove the obsolete third palette completely; color mode is now the only visual theme axis.
scss = re.sub(r'\nhtml\[data-panel-theme="black_gold"\][^{]*\{[^{}]*\}\n', '\n', scss, flags=re.S)
scss_path.write_text(scss, encoding="utf-8")

test_path = Path("app/dashboard/scripts/test-admin-ux.cjs")
test = test_path.read_text(encoding="utf-8")
old_palette = 'assert.ok(dashboardStyles.includes("dashboard palette normalization") && dashboardStyles.includes("--panel-accent-soft") && dashboardStyles.includes(\'html[data-panel-theme="black_gold"]\'), "dashboard palette tokens must define coherent blue and black-gold themes");'
new_palette = 'assert.ok(dashboardStyles.includes("v1.0.6 unified visual language") && dashboardStyles.includes("--panel-accent-soft") && dashboardStyles.includes("--panel-sidebar") && !dashboardStyles.includes(\'html[data-panel-theme="black_gold"]\'), "dashboard palette tokens must define only coherent light and dark themes");'
if old_palette not in test:
    raise RuntimeError("old palette assertion missing")
test = test.replace(old_palette, new_palette, 1)
old_actions = 'assert.ok(usersTablePro.includes(\'flexWrap="wrap"\'), "direct user actions must wrap inside their cell instead of widening the table");'
new_actions = 'assert.ok(usersTablePro.includes("<MenuButton") && usersTablePro.includes("عملیات بیشتر") && usersTablePro.includes(\'label="کپی لینک اشتراک"\') && usersTablePro.includes(\'label="حذف کاربر"\'), "user row must keep primary actions direct and move secondary actions into a compact overflow menu");'
if old_actions not in test:
    raise RuntimeError("old action assertion missing")
test = test.replace(old_actions, new_actions, 1)
test_path.write_text(test, encoding="utf-8")
print("v1.0.6 UI contracts aligned")
