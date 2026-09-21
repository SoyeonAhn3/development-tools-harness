import copy
import json
import subprocess

import pytest

from development_harness import worker_probe as probe


@pytest.fixture
def evidence(tmp_path):
    paths = {name: tmp_path / name for name in ("project", "approval")}
    expected = {"project": True, "approval": False}
    paths["project"].write_text("developer:child\n", encoding="utf-8")
    paths["approval"].write_text(probe.INITIAL, encoding="utf-8")
    parent = {"pid": 1, "writes": {"project": {"outcome": "written"}, "approval": {"outcome": "denied"}},
              "network": {"outcome": "denied"}}
    child = copy.deepcopy(parent)
    child["pid"] = 2
    output = {"parent": parent, "child": child, "child_exit_code": 0}
    process = {"outcome": "finished", "exit_code": 0}
    return paths, expected, output, process


def evaluate(evidence, receipts=()):
    paths, expected, output, process = evidence
    process["stdout"] = json.dumps(output)
    return probe.evaluate_role("developer", process, expected, paths, receipts)


def test_host_receipts_override_reported_network_denial(evidence):
    assert evaluate(evidence)["passed"]
    result = evaluate(evidence, ["developer:child"])
    assert not result["passed"]
    assert not result["checks"]["child:network_denied"]


@pytest.mark.parametrize("generation", ["parent", "child"])
def test_network_connection_fails_candidate_for_either_generation(evidence, generation):
    evidence[2][generation]["network"] = {"outcome": "connected"}
    assert not evaluate(evidence)["passed"]


def test_host_file_evidence_overrides_reported_write_denial(evidence):
    evidence[0]["approval"].write_text("changed", encoding="utf-8")
    result = evaluate(evidence)
    assert not result["passed"]
    assert not result["checks"]["file:approval"]


@pytest.mark.parametrize("problem", ["missing_child", "same_pid", "child_failed", "interrupted", "missing_file"])
def test_incomplete_or_failed_probe_never_passes(evidence, problem):
    paths, expected, output, process = evidence
    if problem == "missing_child":
        del output["child"]
    elif problem == "same_pid":
        output["child"]["pid"] = output["parent"]["pid"]
    elif problem == "child_failed":
        output["child_exit_code"] = 1
    elif problem == "interrupted":
        process["outcome"] = "interrupted"
    elif problem == "missing_file":
        paths["approval"].unlink()
    assert not evaluate(evidence)["passed"]


def test_unknown_worker_version_does_not_inherit_planner_support(tmp_path, monkeypatch):
    binary = tmp_path / "codex.exe"
    binary.write_bytes(b"never executed")
    monkeypatch.setattr(probe, "executable", lambda _: binary)
    monkeypatch.setattr(probe, "command_result", lambda *a: subprocess.CompletedProcess([], 0, "codex-cli 0.154.0", ""))
    monkeypatch.setattr(probe, "_probe_roles", lambda *a: pytest.fail("Unreviewed worker version must not start probes"))
    report = probe.diagnose_workers(tmp_path / "probe")
    assert report["version"] == "codex-cli 0.154.0"
    assert not report["ready"]
    assert not report["execution_enabled"]
    assert report["roles"] == []
    assert "Planner version support is unchanged" in report["next_steps"][0]
    assert json.loads((tmp_path / "probe/report.json").read_text(encoding="utf-8")) == report


def test_existing_probe_evidence_is_never_overwritten(tmp_path):
    (tmp_path / "report.json").write_text("original", encoding="utf-8")
    with pytest.raises(FileExistsError):
        probe.diagnose_workers(tmp_path)
    assert (tmp_path / "report.json").read_text() == "original"


def test_probe_failure_is_saved_without_execution_permission(tmp_path, monkeypatch):
    def missing(_):
        raise OSError("No executable")
    monkeypatch.setattr(probe, "executable", missing)
    report = probe.diagnose_workers(tmp_path / "probe")
    assert not report["ready"]
    assert report["actual_ai_calls"] == 0
    assert "No executable" in report["error"]
    assert (tmp_path / "probe/report.json").is_file()
