from pathlib import Path

ROOT = Path(__file__).resolve().parents[2]

notes = ROOT / "docs/RELEASE_NOTES_v1.0.7.md"
s = notes.read_text()
install = '''\n## نصب و به‌روزرسانی\n\nبرای نصب یا به‌روزرسانی از ابزار مدیریت Marzban استفاده کنید:\n\n```bash\nmarzban update\n```\n'''
if "marzban update" not in s:
    s = s.rstrip() + "\n" + install
notes.write_text(s)

p = ROOT / "tests/test_v102_node_ip_policy.py"
s = p.read_text()
old = '''def test_frontend_exposes_safe_node_ip_source_controls():\n    context = Path("app/dashboard/src/contexts/NodesContext.tsx").read_text(encoding="utf-8")\n    modal = Path("app/dashboard/src/components/NodesModal.tsx").read_text(encoding="utf-8")\n    assert 'z.enum(["direct", "trusted_xff", "proxy_protocol"])' in context\n    assert 'name="ip_source_mode"' in modal\n    assert 'name="trusted_proxy_cidrs"' in modal\n    assert 'nodes.ipSourceRuntimePending' in modal\n'''
new = '''def test_frontend_exposes_safe_node_ip_source_controls():\n    context = Path("app/dashboard/src/contexts/NodesContext.tsx").read_text(encoding="utf-8")\n    workspace = Path("app/dashboard/src/components/NodesManagementWorkspace.tsx").read_text(encoding="utf-8")\n    assert 'z.enum(["direct", "trusted_xff", "proxy_protocol"])' in context\n    assert 'name="ip_source_mode"' in workspace\n    assert 'name="trusted_proxy_cidrs"' in workspace\n    assert 'تنظیمات منبع IP فقط باید برای پراکسی‌های کاملاً مورد اعتماد فعال شود.' in workspace\n'''
if old not in s:
    raise SystemExit("old node IP frontend contract block not found")
s = s.replace(old, new, 1)
p.write_text(s)
