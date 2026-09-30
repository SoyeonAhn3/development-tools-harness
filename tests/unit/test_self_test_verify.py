import json
from pathlib import Path

import pytest

from development_harness.model import HarnessError
from development_harness.self_test_verify import artifact_files, combine, current_profile, reviewed_host
from test_validation_profiles import self_project


@pytest.fixture
def reports(self_project, tmp_path):
    profile = current_profile(self_project)
    paths = []
    for kind in ("isolated", "reviewed-host"):
        directory = tmp_path / kind
        directory.mkdir()
        modules = profile["isolated_modules"] + ([item["path"] for item in profile["host_modules"]]
                                                if kind == "reviewed-host" else [])
        nodes = [name + "::test_example" for name in modules]
        junit, collection = directory / "pytest.xml", directory / "collection.json"
        junit.write_text('<testsuite>' + '<testcase name="example"/>' * len(nodes) + '</testsuite>')
        collection.write_text(json.dumps({"discovered": nodes, "collected": nodes, "passed": nodes, "failed": [], "skipped": [],
            "deselected": [], "collection_errors": [], "exit_status": 0}))
        path = directory / "report.json"
        path.write_text(json.dumps({"kind": kind, "profile": profile, "runner_artifact": "runner-A",
            "passed": True, "tests": len(nodes), "reviewed_input_version": profile["input_version"],
            "validation": {"junit": str(junit), "collection": str(collection)},
            "artifacts": artifact_files([junit, collection])}))
        paths.append(path)
    return self_project, paths


def test_combined_evidence_does_not_accept_phase_and_requires_current_inputs(reports):
    project, paths = reports
    combined = combine(project, "runner-A", *paths)
    assert combined["all_tests_complete"] is True and combined["phase_accepted"] is False
    (project / "tests/unit/test_rules.py").write_text("def test_changed(): pass\n")
    with pytest.raises(HarnessError, match="stale"):
        combine(project, "runner-A", *paths)


@pytest.mark.parametrize("change", ["artifact", "missing-module", "wrong-runner", "missing-host", "unchecked-artifact"])
def test_invalid_or_incomplete_reports_cannot_claim_completion(reports, change):
    project, paths = reports
    record = json.loads(paths[1].read_text())
    if change == "artifact":
        (paths[1].parent / "pytest.xml").write_text("changed")
    elif change == "missing-module":
        collection = paths[1].parent / "collection.json"
        observed = json.loads(collection.read_text())
        observed["collected"].pop()
        observed["passed"].pop()
        collection.write_text(json.dumps(observed))
        record["artifacts"][str(collection.resolve())] = artifact_files([collection])[str(collection.resolve())]
    elif change == "wrong-runner":
        record["runner_artifact"] = "runner-B"
    elif change == "missing-host":
        record["passed"] = False
    else:
        del record["artifacts"][str((paths[1].parent / "collection.json").resolve())]
    paths[1].write_text(json.dumps(record))
    with pytest.raises(HarnessError):
        combine(project, "runner-A", *paths)


def test_host_launch_requires_the_exact_reviewed_input_hash(self_project, tmp_path, monkeypatch):
    monkeypatch.setattr("development_harness.self_test_verify.subprocess.Popen",
                        lambda *a, **k: pytest.fail("Unreviewed code must not launch"))
    with pytest.raises(HarnessError, match="Reviewed input version"):
        reviewed_host(self_project, tmp_path / "result", tmp_path / "A", "A", Path("missing.exe"), "stale", 30)
