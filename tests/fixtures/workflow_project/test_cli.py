"""Passing starting behavior; negative-input handling is the future change."""

from pathlib import Path
import subprocess
import sys

import pytest


@pytest.mark.parametrize("value,expected", [(0, "0\n"), (3, "6\n")])
def test_existing_cli(value, expected):
    result = subprocess.run([sys.executable, str(Path(__file__).with_name("cli.py")), str(value)],
                            capture_output=True, text=True, timeout=10)
    assert result.returncode == 0
    assert result.stdout == expected
    assert result.stderr == ""
