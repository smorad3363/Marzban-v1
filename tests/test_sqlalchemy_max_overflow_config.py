import os
import subprocess
import sys


DATABASE_URL = "mysql+pymysql://user:pass@127.0.0.1:3306/test"


def _config_values(**overrides: str) -> tuple[int, int]:
    env = os.environ.copy()
    env["SQLALCHEMY_DATABASE_URL"] = DATABASE_URL
    env.pop("SQLALCHEMY_MAX_OVERFLOW", None)
    env.pop("SQLIALCHEMY_MAX_OVERFLOW", None)
    env.update(overrides)
    result = subprocess.run(
        [
            sys.executable,
            "-c",
            (
                "import config; "
                "print(config.SQLALCHEMY_MAX_OVERFLOW); "
                "print(config.SQLIALCHEMY_MAX_OVERFLOW)"
            ),
        ],
        check=True,
        capture_output=True,
        text=True,
        env=env,
    )
    correct, legacy_alias = result.stdout.strip().splitlines()[-2:]
    return int(correct), int(legacy_alias)


def test_sqlalchemy_max_overflow_default_is_preserved():
    assert _config_values() == (5, 5)


def test_legacy_misspelling_remains_supported():
    assert _config_values(SQLIALCHEMY_MAX_OVERFLOW="7") == (7, 7)


def test_correct_spelling_is_supported():
    assert _config_values(SQLALCHEMY_MAX_OVERFLOW="11") == (11, 11)


def test_correct_spelling_wins_without_parsing_invalid_legacy_value():
    assert _config_values(
        SQLALCHEMY_MAX_OVERFLOW="13",
        SQLIALCHEMY_MAX_OVERFLOW="not-an-int",
    ) == (13, 13)
