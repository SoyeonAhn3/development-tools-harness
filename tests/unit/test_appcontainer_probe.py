import copy
import json
import subprocess

import pytest

from development_harness import appcontainer_probe as probe
from development_harness.model import HarnessError
from development_harness.windows_appcontainer import ProbeContainer


@pytest.fixture
def evidence(tmp_path):
    paths = {"project": tmp_path / "source", "approval": tmp_path / "approval"}
    paths["project"].write_text("developer:child\n", encoding="utf-8")
    paths["approval"].write_text(probe.INITIAL, encoding="utf-8")
    expected = {"project": True, "approval": False}
    parent = {"pid": 1, "token": dict(probe.TOKEN),
              "writes": {"project": {"outcome": "written"}, "approval": {"outcome": "denied"}},
              "reads": {"project": "read", "approval": "denied"}, "network": {"outcome": "denied"},
              "networks": {name: {"outcome": "denied"} for name in probe.NETWORKS}}
    child = copy.deepcopy(parent)
    child["pid"] = 2
    output = {"parent": parent, "child": child, "child_exit_code": 0}
    process = {"outcome": "finished", "exit_code": 0, "token": dict(probe.TOKEN)}
    return paths, expected, output, process


def evaluate(evidence, receipts=()):
    paths, expected, output, process = evidence
    process["stdout"] = json.dumps(output)
    return probe.evaluate("developer", process, expected, paths, receipts)


@pytest.mark.parametrize("generation", ["parent", "child"])
@pytest.mark.parametrize("network", probe.NETWORKS)
def test_listener_receipt_rejects_falsely_reported_denial(evidence, generation, network):
    assert evaluate(evidence)["passed"]
    result = evaluate(evidence, ["developer:" + generation + ":" + network])
    assert not result["passed"]
    assert not result["checks"][generation + ":" + network + "_denied"]


@pytest.mark.parametrize("problem", ["host_token", "child_token", "read_control", "missing_udp", "missing_child"])
def test_incomplete_permission_evidence_does_not_pass(evidence, problem):
    output, process = evidence[2:]
    if problem == "host_token":
        process["token"]["appcontainer"] = False
    elif problem == "child_token":
        output["child"]["token"]["capability_count"] = 1
    elif problem == "read_control":
        output["parent"]["reads"]["approval"] = "read"
    elif problem == "missing_udp":
        del output["child"]["networks"]["udp6"]
    else:
        del output["child"]
    assert not evaluate(evidence)["passed"]


def test_grants_cannot_change_existing_paths_outside_probe(tmp_path):
    root = tmp_path / "probe"
    root.mkdir()
    other = tmp_path / "existing.txt"
    other.write_text("preserve")
    container = ProbeContainer(root)
    for path in (other, root, root / ".." / "existing.txt"):
        with pytest.raises(HarnessError, match="disposable tree"):
            container.grant(path, write=True)
    assert other.read_text() == "preserve"


def test_diagnosis_failure_is_saved_without_unrestricted_fallback(tmp_path, monkeypatch):
    def fail(_):
        raise subprocess.TimeoutExpired("synthetic setup", 15)
    monkeypatch.setattr(probe, "copy_runtime", fail)
    monkeypatch.setattr(probe, "_roles", lambda *args: pytest.fail("No fallback may execute after setup failure"))
    report = probe.diagnose_appcontainer(tmp_path / "probe")
    assert not report["ready"]
    assert not report["execution_enabled"]
    assert report["actual_ai_calls"] == 0
    assert report["roles"] == []
    assert "timed out" in report["error"]
    assert json.loads((tmp_path / "probe/report.json").read_text(encoding="utf-8")) == report


def test_existing_evidence_is_not_overwritten(tmp_path):
    (tmp_path / "report.json").write_text("original")
    with pytest.raises(FileExistsError):
        probe.diagnose_appcontainer(tmp_path)
    assert (tmp_path / "report.json").read_text() == "original"
