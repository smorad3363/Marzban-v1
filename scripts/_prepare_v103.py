from pathlib import Path


def replace_exact(path: str, old: str, new: str, count: int = 1) -> None:
    p = Path(path)
    text = p.read_text(encoding="utf-8")
    actual = text.count(old)
    assert actual == count, f"{path}: expected {count} copies, found {actual}: {old!r}"
    p.write_text(text.replace(old, new), encoding="utf-8")


Path("VERSION").write_text("1.0.3\n", encoding="utf-8")
replace_exact("app/__init__.py", '__version__ = "1.0.2"', '__version__ = "1.0.3"')
replace_exact(
    "docker-compose.yml",
    "image: ghcr.io/smorad3363/marzban-v1:v1.0.2",
    "image: ghcr.io/smorad3363/marzban-v1:v1.0.3",
)
replace_exact(
    "scripts/marzban.sh",
    'CLI_RELEASE_VERSION="v1.0.2"',
    'CLI_RELEASE_VERSION="v1.0.3"',
)

replace_exact(
    "README.md",
    'sudo bash -c "$(curl -fsSL https://raw.githubusercontent.com/smorad3363/Marzban-v1/v1.0.2/scripts/marzban.sh)" @ install --version v1.0.2 --database mysql',
    'sudo bash -c "$(curl -fsSL https://raw.githubusercontent.com/smorad3363/Marzban-v1/v1.0.3/scripts/marzban.sh)" @ install --version v1.0.3 --database mysql',
)
replace_exact(
    "README.md",
    "Marzban V1.0.2 includes **Built-in Node Runtime V2**.",
    "Marzban V1.0.3 includes **Built-in Node Runtime V2**.",
)
replace_exact(
    "README.md",
    '''On the Node server, copy only the panel client **certificate** (public PEM). Never copy the panel private key. Then install the exact release:\n\n```bash\nsudo bash -c "$(curl -fsSL https://raw.githubusercontent.com/smorad3363/Marzban-v1/v1.0.2/scripts/marzban.sh)" @ node install --version v1.0.2 --client-cert-file /path/to/panel-client.crt\n```''',
    '''On the Node server, copy the Node certificate shown in **Master > Nodes**. Never copy the panel private key. Run the exact release installer; it will ask you to paste the complete PEM certificate from `BEGIN CERTIFICATE` through `END CERTIFICATE`:\n\n```bash\nsudo bash -c "$(curl -fsSL https://raw.githubusercontent.com/smorad3363/Marzban-v1/v1.0.3/scripts/marzban.sh)" @ node install --version v1.0.3\n```\n\nFor unattended automation only, you can still provide an existing PEM file with `--client-cert-file /path/to/panel-client.crt`.''',
)
replace_exact("README.md", "marzban node update --version v1.0.2", "marzban node update --version v1.0.3")

replace_exact(
    "README-fa.md",
    "برای نصب نسخه دقیق V1.0.2 از دستور زیر استفاده کنید:",
    "برای نصب نسخه دقیق V1.0.3 از دستور زیر استفاده کنید:",
)
replace_exact(
    "README-fa.md",
    'sudo bash -c "$(curl -fsSL https://raw.githubusercontent.com/smorad3363/Marzban-v1/v1.0.2/scripts/marzban.sh)" @ install --version v1.0.2 --database mysql',
    'sudo bash -c "$(curl -fsSL https://raw.githubusercontent.com/smorad3363/Marzban-v1/v1.0.3/scripts/marzban.sh)" @ install --version v1.0.3 --database mysql',
)
replace_exact(
    "README-fa.md",
    "در V1.0.2، **Node Runtime V2** داخل خود مرزبان قرار دارد",
    "در V1.0.3، **Node Runtime V2** داخل خود مرزبان قرار دارد",
)
replace_exact(
    "README-fa.md",
    '''روی سرور نود فقط **گواهی عمومی کلاینت پنل** را به‌صورت PEM کپی کنید؛ کلید خصوصی پنل نباید روی نود قرار بگیرد. سپس نسخه دقیق را نصب کنید:\n\n```bash\nsudo bash -c "$(curl -fsSL https://raw.githubusercontent.com/smorad3363/Marzban-v1/v1.0.2/scripts/marzban.sh)" @ node install --version v1.0.2 --client-cert-file /path/to/panel-client.crt\n```''',
    '''از بخش **Nodes** در Master، Certificate نود را کپی کنید؛ کلید خصوصی پنل نباید روی نود قرار بگیرد. سپس دستور زیر را روی سرور نود اجرا کنید. نصب‌کننده خودش از شما می‌خواهد کل PEM را از `BEGIN CERTIFICATE` تا `END CERTIFICATE` paste کنید:\n\n```bash\nsudo bash -c "$(curl -fsSL https://raw.githubusercontent.com/smorad3363/Marzban-v1/v1.0.3/scripts/marzban.sh)" @ node install --version v1.0.3\n```\n\nبرای نصب غیرتعاملی/اتوماتیک، گزینه `--client-cert-file /path/to/panel-client.crt` همچنان پشتیبانی می‌شود.''',
)
replace_exact("README-fa.md", "marzban node update --version v1.0.2", "marzban node update --version v1.0.3")

contract = Path("tests/test_release_contract.py")
text = contract.read_text(encoding="utf-8")
text = text.replace('assert version == "1.0.2"', 'assert version == "1.0.3"')
old_notes = '''    current_notes = Path("docs/RELEASE_NOTES_v1.0.2.md").read_text(encoding="utf-8")\n    assert "Built-in Node Runtime V2" in current_notes\n    assert "durable" in current_notes.lower()\n    assert "Access Group" in current_notes\n    assert "v1.0.0" in current_notes\n'''
new_notes = '''    v102_notes = Path("docs/RELEASE_NOTES_v1.0.2.md").read_text(encoding="utf-8")\n    assert "Built-in Node Runtime V2" in v102_notes\n    assert "durable" in v102_notes.lower()\n    assert "Access Group" in v102_notes\n    assert "v1.0.0" in v102_notes\n\n    current_notes = Path("docs/RELEASE_NOTES_v1.0.3.md").read_text(encoding="utf-8")\n    assert "interactive" in current_notes.lower()\n    assert "--client-cert-file" in current_notes\n    assert "v1.0.2" in current_notes\n'''
assert text.count(old_notes) == 1, "release notes contract context changed"
text = text.replace(old_notes, new_notes)
contract.write_text(text, encoding="utf-8")

Path("docs/RELEASE_NOTES_v1.0.3.md").write_text(
    '''# Marzban v1.0.3\n\nMarzban v1.0.3 is a focused installer UX hotfix on top of the validated v1.0.2 runtime.\n\n## Change\n\n- Restores the familiar **interactive Node certificate paste** flow: when `--client-cert-file` is omitted, `marzban node install` asks for the complete PEM copied from Master > Nodes and finishes input automatically at `END CERTIFICATE`.\n- Keeps `--client-cert-file /path/to/panel-client.crt` available for unattended automation.\n- The pasted certificate is validated as X.509, handled through a mode-600 temporary file, and only the public certificate is stored on the Node. The panel private key is never requested or copied.\n\n## Compatibility\n\n- This is a patch on top of v1.0.2; Node Runtime V2, durable event delivery, Device Limit behavior, CDN/IP-source policy, Access Group ownership, and low-memory defaults are unchanged.\n- Historical V1 lineage remains exactly `v5.2.0 -> v1.0.0`.\n- Published v1.0.0, v1.0.1, and v1.0.2 artifacts remain immutable.\n''',
    encoding="utf-8",
)

# Guard immutable lineage while preparing the patch release.
installer = Path("scripts/marzban.sh").read_text(encoding="utf-8")
assert 'V1_LINEAGE_SOURCE_VERSION="5.2.0"' in installer
assert 'V1_LINEAGE_SOURCE_IMAGE="ghcr.io/smorad3363/marzban-vnext:v5.2.0"' in installer
assert 'V1_LINEAGE_TARGET_VERSION="v1.0.0"' in installer
