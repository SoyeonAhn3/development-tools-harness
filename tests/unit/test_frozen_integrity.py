"""Frozen artifact integrity must fail closed before dispatch or storage creation."""

import json
from pathlib import Path
import zipfile

import pytest

from development_harness.fixed_runner import build_runner, extract_wheel
from development_harness.frozen_entry import MANIFEST, fingerprint, guard_paths, inspect_runner, inventory
from development_harness.model import HarnessError


@pytest.fixture
def frozen_tree(tmp_path):
    root = tmp_path / "A"
    for name in ("run.py", "runtime/python.exe", "tools/codex.exe", "policy.json",
                 "runtime/Lib/site-packages/development_harness/__init__.py"):
        path = root / name
        path.parent.mkdir(parents=True, exist_ok=True)
        path.write_text("original", encoding="utf-8")
    manifest = {"format": 1, "files": inventory(root)}
    manifest["artifact_id"] = fingerprint(manifest)
    (root / MANIFEST).write_text(json.dumps(manifest))
    return root, manifest


@pytest.mark.parametrize("mode", ["change", "delete", "add_startup_hook", "manifest", "hardlink"])
def test_changed_runtime_instructions_or_manifest_are_rejected(frozen_tree, mode, tmp_path):
    root, manifest = frozen_tree
    assert inspect_runner(root) == manifest
    if mode == "change":
        (root / "policy.json").write_text("changed policy")
    elif mode == "delete":
        (root / "tools/codex.exe").unlink()
    elif mode == "add_startup_hook":
        (root / "runtime/Lib/site-packages/injected.pth").write_text("import bad")
    elif mode == "manifest":
        manifest["files"]["policy.json"] = "forged"
        (root / MANIFEST).write_text(json.dumps(manifest))
    else:
        (tmp_path / "outside-policy").hardlink_to(root / "policy.json")
    with pytest.raises(ValueError, match="changed|one link"):
        inspect_runner(root)


@pytest.mark.parametrize("a,b,state", [("A", "A/target", "state"), ("A", ".", "state"),
                                      ("A", "B", "A/state"), ("A", "B", "B/state"),
                                      ("A", "state/B", "state"), ("OneDrive/A", "B", "state")])
def test_runner_project_and_records_must_not_overlap(tmp_path, a, b, state):
    with pytest.raises(ValueError, match="separate|OneDrive"):
        guard_paths(tmp_path / a, tmp_path / b, tmp_path / state)


def test_separate_target_and_state_are_allowed(tmp_path):
    guard_paths(tmp_path / "A", tmp_path / "B", tmp_path / "state")


@pytest.mark.parametrize("name", ["../escape.py", "package.pth", "other_package/__init__.py",
                                  "development_harness/../../outside", "harness.data/scripts/start.py"])
def test_wheel_cannot_escape_or_add_startup_hooks(tmp_path, name):
    wheel = tmp_path / "bad.whl"
    with zipfile.ZipFile(wheel, "w") as archive:
        archive.writestr(name, "bad")
    with pytest.raises(HarnessError, match="wheel member"):
        extract_wheel(wheel, tmp_path / "site")
    assert not (tmp_path / "site").exists()


def test_builder_never_overwrites_an_existing_runner(tmp_path):
    repository, existing = tmp_path / "B", tmp_path / "A"
    repository.mkdir()
    existing.mkdir()
    marker = existing / "preserved.txt"
    marker.write_text("existing runner")
    with pytest.raises(HarnessError, match="already exists"):
        build_runner(repository, existing)
    assert marker.read_text() == "existing runner"


def test_builder_cannot_freeze_into_the_development_tree(tmp_path):
    with pytest.raises(HarnessError, match="outside"):
        build_runner(tmp_path, tmp_path / "A")
