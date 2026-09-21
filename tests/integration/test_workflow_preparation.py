import hashlib
import json
from pathlib import Path
import shutil
import subprocess
import sys
import uuid

import pytest

from development_harness.codex_adapter import executable
from development_harness.model import HarnessError
from development_harness.planning import Planning
from development_harness.project import read_json
from development_harness.store import default_home
from development_harness import worker_probe


FIXTURES = Path(__file__).parents[1] / "fixtures"


def test_workflow_fixture_has_real_passing_baseline_and_preserves_inputs(tmp_path):
    project = tmp_path / "workflow project 한글"
    shutil.copytree(FIXTURES / "workflow_project", project)
    before = {p.name: hashlib.sha256(p.read_bytes()).hexdigest() for p in project.iterdir() if p.is_file()}
    planner = Planning(project, tmp_path / "state")
    planner.register({"version": 1, "spec": "spec.md", "context": ["cli.py", "test_cli.py"],
                      "validation": read_json(FIXTURES / "workflow-checks.json"),
                      "model": "unused-baseline-only", "planner_timeout": 120})
    result = planner.plan(baseline_only=True)
    assert result["stage"] == "planning"
    assert result["baseline_evidence"][0]["tests"] == 2
    assert result["baseline_evidence"][0]["outcome"] == "passed"
    assert planner.status()["actual_ai_call_attempts"] == 0
    for name, digest in before.items():
        assert hashlib.sha256((project / name).read_bytes()).hexdigest() == digest
    # This is the unchanged starting program, not a preimplemented live example.
    negative = subprocess.run([sys.executable, str(project / "cli.py"), "-1"],
                              capture_output=True, text=True, timeout=10)
    assert negative.returncode == 0
    assert negative.stdout == "-2\n"


def test_workflow_doctor_missing_executable_preserves_project_and_run(tmp_path):
    project = tmp_path / "project"
    project.mkdir()
    (project / "value.py").write_text("original\n", encoding="utf-8")
    process = subprocess.run([sys.executable, "-m", "development_harness", "--project", str(project),
                              "--state-dir", str(tmp_path / "state"), "workflow-doctor", "--backend", "codex-unelevated", "--codex-path",
                              str(tmp_path / "missing.exe")], capture_output=True, text=True, timeout=10)
    assert process.returncode == 1, process.stderr
    report = json.loads(process.stdout)
    assert not report["ready"]
    assert not report["execution_enabled"]
    assert report["actual_ai_calls"] == 0
    assert (project / "value.py").read_text() == "original\n"
    assert set(p.name for p in project.iterdir()) == {"value.py"}
    assert Path(report["evidence_directory"], "report.json").is_file()


def test_actual_windows_worker_and_descendant_probe():
    try:
        selected = executable()
    except HarnessError as exc:
        pytest.skip(str(exc))
    # pytest's Windows mode-0700 temp root uses an OWNER RIGHTS ACE, which the
    # restricted token cannot read. Use a fresh normally inherited runtime path,
    # just like workflow-doctor, and retain its evidence without changing ACLs.
    directory = default_home().parent / "test-worker-probes" / uuid.uuid4().hex
    report = worker_probe.diagnose_workers(directory, codex_path=selected)
    if report.get("version") not in worker_probe.REVIEWED_PROBE_VERSIONS:
        pytest.skip("Installed CLI worker contract has not been reviewed")
    assert "error" not in report, report
    assert all(report["checks"].values()), report
    assert len(report["roles"]) == 3
    for role in report["roles"]:
        assert all(value for key, value in role["checks"].items() if "network" not in key), role
        for generation in ("parent", "child"):
            observation = role["observations"][generation]["network"]["outcome"]
            assert observation in {"connected", "denied"}
            if observation == "connected":
                assert role["role"] + ":" + generation in report["network_receipts"]
    assert report["ready"] == all(role["passed"] for role in report["roles"])
    assert report["execution_enabled"] is False
    assert report["actual_ai_calls"] == 0
