from pathlib import Path
import json
import subprocess


def replace_once(path: str, old: str, new: str) -> None:
    p = Path(path)
    text = p.read_text(encoding="utf-8")
    count = text.count(old)
    if count != 1:
        raise SystemExit(f"{path}: expected exactly one match, found {count}: {old[:120]!r}")
    p.write_text(text.replace(old, new, 1), encoding="utf-8")


# Restore the locale byte-for-byte from the parent before this feature so
# pre-existing duplicate keys are not collapsed by JSON parse/re-serialization.
locale_path = Path("app/dashboard/public/statics/locales/fa.json")
base_locale = subprocess.check_output(
    [
        "git",
        "show",
        "cc7a57a1beb632cee439fe245755cbfc463e0351:app/dashboard/public/statics/locales/fa.json",
    ],
    text=True,
)
for key in ("nodes.ipSourceMode", "nodes.ipSourceRuntimePending"):
    if f'"{key}"' in base_locale:
        raise SystemExit(f"unexpected existing locale key: {key}")
entries = {
    "nodes.ipSourceMode": "منبع تشخیص IP کاربر",
    "nodes.ipSourceModeHint": "مشخص کنید این نود IP واقعی کاربر را مستقیم می‌بیند یا پشت CDN / پراکسی مورد اعتماد قرار دارد.",
    "nodes.ipSourceDirect": "اتصال مستقیم",
    "nodes.ipSourceTrustedXff": "CDN / هدر X-Forwarded-For مورد اعتماد",
    "nodes.ipSourceProxyProtocol": "Reverse Proxy با PROXY Protocol",
    "nodes.cdnProvider": "ارائه‌دهنده CDN / پراکسی",
    "nodes.selectCdnProvider": "انتخاب ارائه‌دهنده",
    "nodes.customProxy": "پراکسی سفارشی",
    "nodes.trustedProxyCidrs": "شبکه‌های پراکسی مورد اعتماد (CIDR)",
    "nodes.trustedProxyCidrsHint": "فقط IPهای واسطی که واقعاً تحت کنترل شما یا ارائه‌دهنده معتبر هستند وارد کنید؛ هر خط یک CIDR.",
    "nodes.ipSourceRuntimePending": "این سیاست اکنون ذخیره می‌شود، اما تا فعال‌شدن Node Runtime امن V1.0.2 به هدرهای واسط برای اعمال محدودیت دستگاه اعتماد نمی‌شود.",
}
if not base_locale.endswith("\n}"):
    raise SystemExit("unexpected fa.json ending")
locale_lines = [
    f"  {json.dumps(key, ensure_ascii=False)}: {json.dumps(value, ensure_ascii=False)}"
    for key, value in entries.items()
]
locale_path.write_text(
    base_locale[:-2] + ",\n" + ",\n".join(locale_lines) + "\n}\n",
    encoding="utf-8",
)

# Repair escaped newlines in the TypeScript Textarea without changing layout.
replace_once(
    "app/dashboard/src/components/NodesModal.tsx",
    '''                      value={(field.value || []).join("
")}
''',
    '''                      value={(field.value || []).join("\\n")}
''',
)
replace_once(
    "app/dashboard/src/components/NodesModal.tsx",
    '''                            .split(/[
,]+/)
''',
    '''                            .split(/[\\n,]+/)
''',
)
replace_once(
    "app/dashboard/src/components/NodesModal.tsx",
    '''                      placeholder={"173.245.48.0/20
2400:cb00::/32"}
''',
    '''                      placeholder={"173.245.48.0/20\\n2400:cb00::/32"}
''',
)
