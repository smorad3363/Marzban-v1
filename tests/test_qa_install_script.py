"""Keep disposable QA install repeatable, non-destructive, and syntax-valid."""
from pathlib import Path
import subprocess


def test_qa_script_bash_syntax_and_guards():
    script = Path(__file__).resolve().parents[1] / "scripts" / "install-qa.sh"
    subprocess.run(["bash", "-n", str(script)], check=True)
    source = script.read_text()
    assert 'set -Eeuo pipefail' in source
    assert 'SOURCE_SHA="f71bf44d72a5e759384691a04769739c19b5921a"' in source
    assert "git -C \"$SRC_DIR\" rev-parse HEAD" in source
    assert 'Existing data at $directory' in source
    assert 'UVICORN_HOST=127.0.0.1' in source
    assert "docker build --pull --tag" in source
    assert "docker compose --project-name" in source
    assert "This is a test installation, not a published stable release." in source
