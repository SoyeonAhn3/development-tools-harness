import json
import hashlib
from pathlib import Path
import subprocess
import sys

import pytest


def call(project, state, *args):
    return subprocess.run([sys.executable, "-m", "development_harness", "--project", str(project),
                           "--state-dir", str(state), *args], capture_output=True, text=True, timeout=30)


@pytest.mark.parametrize("test_source,outcome", [
    ("def test_ok():\n    assert 1 == 1\n", "passed"),
    ("def test_bad():\n    assert 1 == 2\n", "failed"),
    ("VALUE = 1\n", "no_tests"),
    ("import pytest\n@pytest.mark.skip(reason='fixture')\ndef test_skip(): pass\n", "no_tests"),
])
def test_cli_registration_and_real_baseline(tmp_path, test_source, outcome):
    project = tmp_path / "project 한글"
    project.mkdir()
    (project / "spec.md").write_text("# Fixture\nAdd input validation.")
    (project / "test_case.py").write_text(test_source)
    commands = tmp_path / "checks.json"
    commands.write_text(json.dumps([{"argv": [sys.executable, "-m", "pytest", "-q"], "kind": "pytest", "timeout": 15}]))
    state = tmp_path / "state"
    registered = call(project, state, "register", "--spec", "spec.md", "--model", "test-model", "--validation", str(commands))
    assert registered.returncode == 0, registered.stderr
    baseline = call(project, state, "baseline")
    result = json.loads(baseline.stdout)
    assert baseline.returncode == (0 if outcome == "passed" else 1), baseline.stderr
    assert result["attempts"][-1]["outcome"] == outcome
    assert result["actual_ai_call_attempts"] == 0
    assert result["stage"] == ("planning" if outcome == "passed" else "baseline_pending")
    blocked = call(project, state, "run")
    assert blocked.returncode == 2
    assert "planning-only" in blocked.stderr
    assert call(project, state, "plan-cancel").returncode == 0


def test_real_installed_codex_capability_probe(tmp_path):
    # No AI service call: a loopback provider forces unavailable tools into the real CLI.
    from development_harness.codex_adapter import CodexPlanner, default_model, executable
    from development_harness.model import HarnessError
    try:
        executable()
        model = default_model()
    except HarnessError as exc:
        pytest.skip(str(exc))
    result = CodexPlanner(model, tmp_path / "permission-probe").verify()
    assert set(result["tool_manifest"]) <= {"request_user_input"}
    assert "apply_patch" in result["rejected_tools"]
    assert result["probe_actual_ai_calls"] == 0


@pytest.mark.parametrize("interruption", ["timeout", "keyboard"])
def test_adapter_interruption_stops_actual_worker(tmp_path, interruption):
    from development_harness.codex_adapter import CodexPlanner
    from development_harness.processes import alive
    # Exercise the real adapter lifecycle with an inert Python process; no AI call.
    adapter = CodexPlanner.__new__(CodexPlanner)
    adapter.exe, adapter.model, adapter.directory = Path(sys.executable), "fixture", tmp_path
    adapter.policy = {"binary_hash": hashlib.sha256(adapter.exe.read_bytes()).hexdigest()}
    adapter.arguments = lambda _: [sys.executable, "-c", "import time; time.sleep(60)"]
    attempt = {"id": "interruption-fixture"}
    def launched(record):
        assert alive(record["process"])
        if interruption == "keyboard":
            raise KeyboardInterrupt
    if interruption == "keyboard":
        with pytest.raises(KeyboardInterrupt):
            adapter.generate("fixture", {}, attempt, launched, timeout=0.1)
    else:
        assert adapter.generate("fixture", {}, attempt, launched, timeout=0.1) is None
    assert not alive(attempt["process"])
    assert attempt["outcome"] == "interrupted"
    assert attempt["ended"] is None
    assert attempt["duration"] is None
