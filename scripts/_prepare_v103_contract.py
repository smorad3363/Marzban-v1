from pathlib import Path

p = Path("tests/test_installer_v1_contract.sh")
text = p.read_text(encoding="utf-8")
replacements = {
    'ghcr.io/smorad3363/marzban-v1:v1.0.2': 'ghcr.io/smorad3363/marzban-v1:v1.0.3',
    'runtime_app_version() { printf \'%s\\n\' "1.0.2"; }': 'runtime_app_version() { printf \'%s\\n\' "1.0.3"; }',
    'test "$1" = "v1.0.2"': 'test "$1" = "v1.0.3"',
    'CLI version: v1.0.2': 'CLI version: v1.0.3',
    'Runtime app version: 1.0.2': 'Runtime app version: 1.0.3',
}
for old, new in replacements.items():
    count = text.count(old)
    assert count >= 1, f"missing fixture text: {old}"
    text = text.replace(old, new)
p.write_text(text, encoding="utf-8")

# The historical lineage assertions near the top must remain untouched.
text = p.read_text(encoding="utf-8")
assert '"5.2.0" \\\n  "v1.0.0"' in text
assert '! is_allowed_v1_lineage_transition "5.2.0" "v1.0.1"' in text
