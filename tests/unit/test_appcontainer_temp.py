"""Scope and startup failures for the private validation-runtime hook."""

import os
from pathlib import Path
import subprocess

import pytest

from development_harness.appcontainer_temp import _destination, require


@pytest.mark.parametrize("name", ["../outside", "../scratch-sibling/child", "."])
def test_other_paths_never_select_the_compatibility_operation(tmp_path, name):
    scratch = tmp_path / "scratch"
    scratch.mkdir()
    assert _destination(scratch / name, scratch) is None


@pytest.mark.parametrize("name", ["stream:alternate", "trailing.", "trailing ", "CON"])
def test_device_and_ambiguous_names_are_rejected(tmp_path, name):
    with pytest.raises(PermissionError, match="Unsupported"):
        _destination(tmp_path / name, tmp_path)


def test_directory_junction_is_rejected_even_when_it_points_inside_scratch(tmp_path):
    scratch = tmp_path / "scratch"
    target = scratch / "target"
    target.mkdir(parents=True)
    link = scratch / "link"
    result = subprocess.run([str(Path(os.environ["SystemRoot"]) / "System32/cmd.exe"),
                             "/d", "/c", "mklink", "/J", str(link), str(target)],
                            capture_output=True, creationflags=subprocess.CREATE_NO_WINDOW)
    assert result.returncode == 0, result.stderr
    assert link.is_junction()
    with pytest.raises(PermissionError, match="Linked"):
        _destination(link / "new-private-directory", scratch)
    assert not (target / "new-private-directory").exists()


def test_validation_cannot_proceed_without_the_startup_hook(tmp_path):
    with pytest.raises(RuntimeError, match="not initialized"):
        require(tmp_path)
