"""Result reports expose real evidence and remain read-only on every outcome."""

import copy
import json
from pathlib import Path

import pytest

from development_harness.files import snapshot
from development_harness.planning import Planning
from development_harness.results import report
from test_workflow import FIRST, admitted_factory, developer, isolated_factory, reviewer, scripted_workers
from test_workflow_resume import PassingValidator, crash


def read_report(workflow):
    before = workflow.get()
    events = workflow.store.events(before["id"])
    files = snapshot(workflow.project)
    database = workflow.store.path.read_bytes()
    value = report(workflow)
    assert workflow.get() == before
    assert workflow.store.events(before["id"]) == events
    assert snapshot(workflow.project) == files
    assert workflow.store.path.read_bytes() == database
    assert json.loads(json.dumps(value, allow_nan=False)) == value
    return value


def complete(workflow, validator):
    worker = scripted_workers([developer(text=FIRST), reviewer()])
    run = workflow.execute(worker_factory=worker, validator_factory=validator)
    assert run["stage"] == "technically_complete", run.get("reason")
    assert not worker.pending
    return run


def test_success_report_links_actual_artifacts_and_distinguishes_acceptance(admitted_factory, isolated_factory):
    workflow = admitted_factory(tasks=1)
    run = complete(workflow, isolated_factory)
    result = read_report(workflow)
    assert result["kind"] == "workflow_result" and result["schema_version"] == 1
    assert result["run_id"] == run["id"] and result["outcome"] == "success"
    assert result["technical_complete"] is True
    assert result["acceptance"]["accepted"] is False
    assert result["acceptance"]["ready"] is True, result["acceptance"]
    assert result["content"]["actual_version"] == run["content_version"]
    assert result["unexpected_changes"] == []
    assert [item["path"] for item in result["delivered_files"]] == ["value.py"]
    delivered = result["delivered_files"][0]
    assert delivered["change"] == "modified" and delivered["current"] is True
    assert delivered["task_ids"] == ["T1"]
    assert len(delivered["patch_records"]) == 1
    assert all(item["current"] and item["outcome"] == "passed" for item in result["validation"])
    final = [item for item in result["validation"] if item["final"]]
    assert [item["id"] for item in final] == run["execution"]["final_validation_ids"]
    for key in ("record", "junit", "log", "stderr", "permission_report"):
        location = final[0]["evidence"][key]
        assert location["exists"] is True and Path(location["path"]).is_file()
    for entry in result["evidence"]["attempts"]:
        for location in entry["artifacts"].values():
            assert location["exists"] is True and Path(location["path"]).is_file()
    assert result["evidence"]["database"]["path"] == str(workflow.store.path)
    assert all(item["exists"] for item in result["evidence"]["planning_artifacts"])
    assert result["metrics"]["confirmed_ai_calls"] == 2
    assert result["metrics"]["by_role"]["developer"]["confirmed_ai_calls"] == 1
    assert result["metrics"]["usage"] is result["metrics"]["cost"] is None
    assert result["tasks"][0]["acceptance"] == run["tasks"][0]["acceptance"]
    assert result["tasks"][0]["verification"] == run["tasks"][0]["verification"]
    assert result["validation_commands"] == run["policy"]["validation"]


def test_failure_report_keeps_delivered_files_and_actual_stop_evidence(admitted_factory):
    workflow = admitted_factory(tasks=1, max_corrections=0)
    class Failed(PassingValidator):
        def run(self, *args, **kwargs):
            return super().run(*args, **kwargs) | {"outcome": "failed", "failure_kind": "code", "exit_code": 1}
    workflow.execute(worker_factory=scripted_workers([developer(text=FIRST)]), validator_factory=Failed)
    result = read_report(workflow)
    assert result["outcome"] == "failure" and result["stage"] == "failed"
    assert result["technical_complete"] is False and result["acceptance"]["ready"] is False
    assert "Correction limit" in result["reason"]
    assert result["delivered_files"][0]["path"] == "value.py"
    assert result["validation"][-1]["outcome"] == "failed"
    assert result["validation"][-1]["failure_kind"] == "code"
    assert result["tasks"][0]["completed"] is False


def test_permission_report_preserves_failed_attempt_and_unknown_duration(admitted_factory):
    workflow = admitted_factory(tasks=1)
    class Denied:
        def __init__(self, directory):
            pass
        def verify(self):
            raise PermissionError("Validation permission denied in fixture")
    workflow.execute(worker_factory=scripted_workers([developer(text=FIRST)]), validator_factory=Denied)
    result = read_report(workflow)
    assert result["outcome"] == "permission_failure"
    assert "permission denied" in result["reason"]
    assert result["validation"][-1]["outcome"] == "unverified"
    assert result["validation"][-1]["duration"] is None
    assert result["metrics"]["duration"] is None
    assert result["tasks"][0]["corrections"] == 0


@pytest.mark.parametrize("mode", ["response_saved", "dispatch_uncertain", "partial_patch"])
def test_interrupted_report_preserves_uncertainty_and_partial_delivery(admitted_factory, mode):
    workflow = admitted_factory(tasks=1)
    run = crash(workflow, mode)
    result = read_report(workflow)
    assert result["outcome"] == "interrupted"
    assert result["acceptance"]["ready"] is False
    assert result["technical_complete"] is False
    assert result["delivered_files"] == []
    assert result["metrics"]["ai_dispatch_attempts"] == 1
    if mode == "dispatch_uncertain":
        assert result["metrics"]["total_ai_calls"] is None
        assert result["recovery"]["action"] == "blocked"
        response = result["evidence"]["attempts"][0]["artifacts"]["response"]
        assert response["exists"] is False
    elif mode == "partial_patch":
        assert result["partial_implementation"] == run["execution"]["patch_pending"]
        assert result["unexpected_changes"] == ["value.py"]
        assert result["recovery"]["action"] == "repair"
        assert "inspection_error" in result
    else:
        assert result["recovery"]["action"] == "reuse"
        assert result["evidence"]["attempts"][0]["artifacts"]["response"]["exists"]


def test_user_edit_after_completion_invalidates_report_evidence_without_hiding_results(admitted_factory, isolated_factory):
    workflow = admitted_factory(tasks=1)
    run = complete(workflow, isolated_factory)
    (workflow.project / "value.py").write_text("# User change after verification.\n", encoding="utf-8")
    result = read_report(workflow)
    assert result["outcome"] == "unverified" and result["technical_complete"] is False
    assert "Unexpected file changes" in result["inspection_error"]
    assert result["unexpected_changes"] == ["value.py"]
    assert result["content"]["recorded_version"] == run["content_version"]
    assert result["content"]["actual_version"] != run["content_version"]
    assert result["acceptance"]["ready"] is False
    assert result["delivered_files"][0]["current"] is False
    assert all(item["current"] is False for item in result["validation"])


def test_missing_final_artifact_is_explicit_and_prevents_acceptance(admitted_factory, isolated_factory):
    workflow = admitted_factory(tasks=1)
    run = complete(workflow, isolated_factory)
    final = next(item for item in run["attempts"] if item["id"] == run["execution"]["final_validation_ids"][0])
    Path(final["junit"]).unlink()
    result = read_report(workflow)
    reported = next(item for item in result["validation"] if item["id"] == final["id"])
    assert reported["evidence"]["junit"] == {"path": final["junit"], "exists": False}
    assert result["outcome"] == "unverified" and result["technical_complete"] is False
    assert result["acceptance"]["ready"] is False
    assert result["acceptance"]["blockers"]


def test_mandatory_findings_are_reported_with_history_and_evidence(admitted_factory):
    workflow = admitted_factory(tasks=1, max_corrections=0)
    workflow.execute(worker_factory=scripted_workers([developer(), reviewer(finding=True)]),
                     validator_factory=PassingValidator)
    result = read_report(workflow)
    assert result["outcome"] == "failure"
    assert len(result["unresolved_findings"]) == 1
    finding = result["unresolved_findings"][0]
    assert finding["required"] and finding["status"] == "open"
    assert finding["evidence"] and finding["recommendation"] and finding["history"]
    assert result["metrics"]["blocking_findings"] == [finding["id"]]


def test_unchanged_task_is_not_credited_with_an_earlier_tasks_file_change(admitted_factory):
    workflow = admitted_factory(tasks=2)
    worker = scripted_workers([developer(text=FIRST), reviewer(), developer("T2"), reviewer("T2")])
    workflow.execute(worker_factory=worker, validator_factory=PassingValidator)
    result = read_report(workflow)
    assert result["delivered_files"][0]["task_ids"] == ["T1"]
    assert len(result["delivered_files"][0]["patch_records"]) == 1
    assert [item["completed"] for item in result["tasks"]] == [True, True]


def test_reuse_requirement_without_task_is_reported_as_unverified(admitted_factory, tmp_path):
    workflow = admitted_factory(tasks=1)
    workflow.cancel()
    planner = Planning(workflow.project, workflow.store.home)
    source = planner.get()
    plan = copy.deepcopy(source["versions"][-1]["plan"])
    requirement = copy.deepcopy(plan["requirements"][0])
    requirement.update(id="R2", disposition="reuse")
    plan["requirements"].append(requirement)
    revision = tmp_path / "reuse-plan.json"
    revision.write_text(json.dumps(plan), encoding="utf-8")
    planner.revise(revision)
    planner.approve()
    workflow.prepare()
    workflow.approve()
    complete(workflow, PassingValidator)
    result = read_report(workflow)
    assert len(result["reuse_evidence"]) == 1
    reused = result["reuse_evidence"][0]
    assert reused["requirement_id"] == "R2"
    assert reused["status"] != "passed"
    assert result["acceptance"]["ready"] is False
    assert all("R2" not in task["requirements"] for task in result["tasks"])


def test_manual_procedure_and_confirmation_are_distinct_from_technical_completion(admitted_factory, isolated_factory):
    workflow = admitted_factory(tasks=1)
    workflow.cancel()
    definition = {"id": "M1", "requirement_ids": ["R1"],
                  "procedure": "Inspect the value shown by the prepared example.",
                  "expected": "The shown value is 1."}
    workflow.prepare(manual_checks=[definition])
    workflow.approve()
    complete(workflow, isolated_factory)
    pending = read_report(workflow)
    assert pending["outcome"] == "success" and pending["technical_complete"] is True
    assert pending["acceptance"]["ready"] is False
    assert len(pending["manual_checks"]) == 1
    check = pending["manual_checks"][0]
    assert check["id"] == "M1" and check["status"] == "missing"
    assert check["procedure"] == definition["procedure"] and check["expected"] == definition["expected"]
    workflow.record_manual("M1", "passed", "Fixture operator confirmed the expected value.")
    confirmed = read_report(workflow)
    assert confirmed["manual_checks"][0]["status"] == "passed"
    assert confirmed["manual_checks"][0]["evidence"]["source"] == "user"
    assert confirmed["acceptance"]["ready"] is True and confirmed["acceptance"]["accepted"] is False
    workflow.accept()
    accepted = read_report(workflow)
    assert accepted["stage"] == "accepted" and accepted["outcome"] == "success"
    assert accepted["acceptance"]["accepted"] is True


@pytest.mark.parametrize("kind", ["defect", "requirements"])
def test_report_preserves_original_feedback_and_routing_history(admitted_factory, kind):
    workflow = admitted_factory(tasks=1)
    complete(workflow, PassingValidator)
    text = "  Keep the approved value behavior.\nPreserve the existing tests.\n"
    options = {"task_id": "T1"} if kind == "defect" else {}
    routed = workflow.feedback(text, kind=kind, **options)
    result = read_report(workflow)
    feedback = result["feedback"][0]
    assert feedback["text"] == text
    assert feedback["kind"] == kind
    assert feedback["routing_outcome"] == ("correction_requested" if kind == "defect" else "replanning_required")
    assert feedback["previous_completion"]["stage"] == "technically_complete"
    assert result["unresolved_feedback"] == [feedback]
    assert result["acceptance"]["ready"] is False
    if kind == "defect":
        complete(workflow, PassingValidator)
        corrected = read_report(workflow)
        assert corrected["feedback"][0]["text"] == text
        assert corrected["feedback"][0]["routing_outcome"] == feedback["routing_outcome"]
        assert corrected["feedback"][0]["outcome"] == "corrected"
        assert len(corrected["feedback"][0]["history"]) == 2
        assert corrected["unresolved_feedback"] == []
        assert corrected["feedback"][0]["resolution"]["final_validation_ids"] == workflow.get()["execution"]["final_validation_ids"]
    else:
        assert result["stage"] == "replanning_required"
        assert result["outcome"] == "replanning_required"
        assert result["feedback"] == routed["feedback"]
