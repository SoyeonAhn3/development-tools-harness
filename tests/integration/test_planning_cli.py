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
    assert result["stdin_verified"] is True
    assert result["output_schema_verified"] is True
    assert result["json_response_verified"] is True
    assert result["ready"] is True


def test_doctor_missing_selected_cli_reports_actionable_json(tmp_path):
    project = tmp_path / "project"
    project.mkdir()
    missing = tmp_path / "selected CLI" / "codex.exe"
    result = call(project, tmp_path / "state", "doctor", "--codex-path", str(missing), "--model", "test")
    assert result.returncode == 1, result.stderr
    report = json.loads(result.stdout)
    assert report["executable"] == str(missing)
    assert report["ready"] is False
    assert report["checks"]["executable"]["status"] == "failed"
    assert report["checks"]["probe"]["status"] == "not_run"
    assert report["next_steps"]


def test_adapter_long_runtime_path_preserves_attempt_artifacts(tmp_path):
    from development_harness.codex_adapter import CodexPlanner

    # P2-01: a 217-character call directory made the old schema path 262 characters.
    padding = 217 - len(str(tmp_path)) - 34
    assert padding > 0, "Use a shorter pytest temporary directory for the 217-character fixture."
    parent = tmp_path / ("p" * padding)
    worker = """
import json
from pathlib import Path
import sys

schema = json.loads(Path(sys.argv[1]).read_text(encoding="utf-8"))
prompt = sys.stdin.read()
print(json.dumps({"type": "item.completed", "item": {
    "type": "agent_message", "text": json.dumps({"schema": schema, "prompt": prompt})}}))
print(json.dumps({"type": "turn.completed", "usage": {"input_tokens": 1}}))
print(prompt, file=sys.stderr)
"""
    artifacts = []
    for index in range(2):
        call_id = str(index) * 32
        directory = parent / call_id
        directory.mkdir(parents=True)
        assert len(str(directory)) == 217
        assert len(str(directory / (call_id + ".schema.json"))) == 262
        # Keep the real file/subprocess lifecycle, using a local Python worker with no AI calls.
        adapter = CodexPlanner.__new__(CodexPlanner)
        adapter.exe, adapter.model, adapter.directory = Path(sys.executable), "fixture", directory
        adapter.policy = {"binary_hash": hashlib.sha256(adapter.exe.read_bytes()).hexdigest()}
        adapter.arguments = lambda schema: [sys.executable, "-c", worker, str(schema)]
        attempt = {"id": call_id, "dispatched": False}
        schema = {"type": "object", "title": f"attempt-{index}"}
        prompt = f"attempt-{index}"

        def launched(record):
            record["dispatched"] = True
            assert all(Path(record[key]).is_file() for key in ("schema", "log", "stderr"))

        assert adapter.generate(prompt, schema, attempt, launched, timeout=15) == {
            "schema": schema, "prompt": prompt}
        assert attempt["id"] == call_id
        assert attempt["dispatched"] is True
        assert attempt["outcome"] == "responded"
        assert attempt["exit_code"] == 0
        assert attempt["usage"] == {"input_tokens": 1}
        for key in ("schema", "log", "stderr"):
            path = Path(attempt[key])
            assert path.parent == directory
            assert len(str(path)) < 260
            artifacts.append((path, path.read_bytes()))
        assert json.loads(Path(attempt["schema"]).read_text(encoding="utf-8")) == schema
        assert Path(attempt["stderr"]).read_text(encoding="utf-8").strip() == prompt

    # A later call must keep the earlier call's schema and logs intact.
    assert len({path for path, _ in artifacts}) == 6
    assert all(path.read_bytes() == original for path, original in artifacts)


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
