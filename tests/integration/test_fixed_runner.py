"""Actual offline installation, import independence and protected B test processes."""

import json
import os
from pathlib import Path
import subprocess
import sys
import uuid

import pytest

from development_harness.fixed_runner import build_runner
from development_harness.frozen_entry import inspect_runner
from development_harness.store import default_home


@pytest.fixture(scope="module")
def fixed_runner():
    directory = default_home().parent / "t8-tests" / uuid.uuid4().hex[:10]
    root = directory / "A"
    info = build_runner(Path(__file__).resolve().parents[2], root)
    return root, info


def invoke(root, *arguments, cwd=None, env=None):
    result = subprocess.run([str(root / "runtime/python.exe"), "-I", "-B", str(root / "run.py"), *arguments],
                            cwd=cwd or root.parent, env=env, capture_output=True, text=True,
                            timeout=60, creationflags=subprocess.CREATE_NO_WINDOW)
    return result


def test_installed_origins_ignore_b_source_and_python_environment(fixed_runner):
    root, expected = fixed_runner
    project = root.parent / "import-trap"
    project.mkdir()
    (project / "development_harness").mkdir()
    (project / "development_harness/__init__.py").write_text("raise RuntimeError('B imported')")
    (project / "sitecustomize.py").write_text("raise RuntimeError('B startup hook')")
    (project / "pytest.py").write_text("raise RuntimeError('B pytest')")
    env = os.environ | {"PYTHONPATH": str(project), "PYTHONHOME": str(project),
                        "DEVELOPMENT_HARNESS_CODEX_PATH": str(project / "bad.exe")}
    result = invoke(root, "--runner-info", cwd=project, env=env)
    assert result.returncode == 0, result.stderr
    assert json.loads(result.stdout) == expected
    inspect_runner(root)


@pytest.mark.parametrize("target", ["project", "state"])
def test_cli_refuses_to_open_its_own_installation_as_writable_state(fixed_runner, target):
    root, _ = fixed_runner
    project = root if target == "project" else root.parent / "outside-project"
    project.mkdir(exist_ok=True)
    state = root / "forbidden-state" if target == "state" else root.parent / "unused-state"
    result = invoke(root, "--project", str(project), "--state-dir", str(state), "status")
    assert result.returncode == 2 and "separate" in result.stderr
    assert not state.exists()


def test_cli_rejects_changed_policy_before_dispatch_and_preserves_candidate(fixed_runner):
    root, _ = fixed_runner
    path = root / "policy.json"
    original = path.read_bytes()
    try:
        path.write_bytes(original + b" ")
        result = invoke(root, "--runner-info")
        assert result.returncode == 2 and "content changed" in result.stderr
        assert path.read_bytes() == original + b" "
    finally:
        path.write_bytes(original)
    inspect_runner(root)


def test_cli_cannot_replace_the_pinned_adapter(fixed_runner):
    root, _ = fixed_runner
    project = root.parent / "adapter-project"
    project.mkdir()
    state = root.parent / "adapter-state"
    result = invoke(root, "--project", str(project), "--state-dir", str(state),
                    "workflow-run", "--codex-path", sys.executable)
    assert result.returncode == 2 and "pinned Codex" in result.stderr
    assert not state.exists()


def test_actual_b_code_and_descendants_only_write_disposable_records(fixed_runner):
    from development_harness.fixed_runner_verify import verify_permissions

    root, _ = fixed_runner
    repository = Path(__file__).resolve().parents[2]
    evidence = verify_permissions(repository, root, root.parent / "permissions")
    assert evidence["passed"]
    assert evidence["parent"]["pid"] != evidence["child"]["pid"]
    assert all(value == "denied" for key in ("parent", "child") for value in evidence[key]["writes"].values())
    assert evidence["temporary_database"] is True
    inspect_runner(root)
