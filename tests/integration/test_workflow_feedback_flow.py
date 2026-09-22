"""T6 feedback through real subprocess roles, isolated checks and public APIs.

Role outputs are deterministic local fixtures; no AI service is called.
"""

import copy
import json
from pathlib import Path
import subprocess
import sys
import time

import pytest

from development_harness.model import HarnessError, digest
from development_harness.planning import Planning
from development_harness.project import content_baseline
from development_harness.workflow_acceptance import completion_id
from test_workflow import (FINAL, FIRST, admitted_factory, developer, isolated_factory, reviewer,
                           scripted_workers)


def run(workflow, worker, validator, *, steps=None):
    result = workflow.execute(worker_factory=worker, validator_factory=validator, steps=steps)
    assert result["stage"] in {"executing", "technically_complete"}, result.get("reason")
    return result


def call(workflow, *arguments):
    return subprocess.run([sys.executable, "-m", "development_harness", "--project", str(workflow.project),
        "--state-dir", str(workflow.store.home), *arguments], capture_output=True, text=True,
        encoding="utf-8", timeout=45, creationflags=subprocess.CREATE_NO_WINDOW)


def test_defect_reopens_target_then_rechecks_completed_suffix_without_extra_developer(admitted_factory, isolated_factory):
    workflow = admitted_factory(tasks=2)
    initial_worker = scripted_workers([developer(text=FIRST), reviewer(), developer(task="T2", text=FINAL), reviewer(task="T2")])
    initial = run(workflow, initial_worker, isolated_factory)
    assert initial["stage"] == "technically_complete" and not initial_worker.pending
    original_attempts = copy.deepcopy(initial["attempts"])
    original_patches = copy.deepcopy(initial["execution"]["patches"])
    original_before = {key: copy.deepcopy(value["before"]) for key, value in initial["execution"]["task_states"].items()}
    original_approval = copy.deepcopy(initial["approval"])
    original_completion = completion_id(initial)
    old_wait = next(item for item in initial["waits"] if item["reason"] == "result_acceptance")
    text = "  Preserve both approved values when handling the corrected input path.\nCheck the original requirement again.  "
    routed = workflow.feedback(text, kind="defect", task_id="T1", feedback_id="user-defect")
    assert routed["feedback"][0]["text"] == text
    assert routed["feedback"][0]["outcome"] == "correction_requested"
    assert routed["execution"]["feedback_rechecks"] == ["T2"]
    assert routed["execution"]["corrections"] == {"T1": 1, "T2": 0}
    closed = next(item for item in routed["waits"] if item["id"] == old_wait["id"])
    assert closed["ended"] == routed["feedback"][0]["received_at"]
    assert workflow.feedback(text, kind="defect", task_id="T1", feedback_id="user-defect") == routed

    fixed = FINAL + "# Preserve both approved values after the scoped correction.\n"
    correction_worker = scripted_workers([developer(text=fixed), reviewer(), reviewer(task="T2")])
    target_done = run(workflow, correction_worker, isolated_factory, steps=3)
    assert target_done["execution"]["completed_tasks"] == ["T1"]
    assert target_done["execution"]["stage"] == "validation"
    assert target_done["feedback"][0]["outcome"] == "correction_requested"
    assert correction_worker.calls[0]["packet"]["feedback"]["evidence"][0]["text"] == text
    suffix_done = run(workflow, correction_worker, isolated_factory, steps=2)
    assert suffix_done["execution"]["stage"] == "final_validation"
    assert suffix_done["feedback"][0]["outcome"] == "correction_requested"
    assert not suffix_done["execution"]["final_validation_ids"]
    final = run(workflow, correction_worker, isolated_factory, steps=1)
    assert final["stage"] == "technically_complete" and not correction_worker.pending
    assert [(item["role"], item["task"]) for item in correction_worker.calls] == [
        ("developer", "T1"), ("reviewer", "T1"), ("reviewer", "T2")]
    assert final["attempts"][:len(original_attempts)] == original_attempts
    assert final["execution"]["patches"][:len(original_patches)] == original_patches
    assert final["approval"] == original_approval
    assert final["execution"]["corrections"] == {"T1": 1, "T2": 0}
    assert final["execution"]["completed_tasks"] == ["T1", "T2"]
    assert final["execution"]["feedback_rechecks"] == []
    assert {key: value["before"] for key, value in final["execution"]["task_states"].items()} == original_before
    assert final["feedback"][0]["text"] == text
    assert final["feedback"][0]["routing_outcome"] == "correction_requested"
    assert final["feedback"][0]["outcome"] == "corrected"
    assert final["feedback"][0]["resolution"]["final_validation_ids"] == final["execution"]["final_validation_ids"]
    assert completion_id(final) != original_completion
    waits = [item for item in final["waits"] if item["reason"] == "result_acceptance"]
    assert len(waits) == 2 and waits[0]["ended"] is not None and waits[1]["ended"] is None
    report = workflow.report()
    assert report["feedback"] == final["feedback"] and not report["unresolved_feedback"]
    assert report["acceptance"]["ready"], report["acceptance"]["blockers"]


def test_unchanged_correction_invalidates_manual_confirmation_by_new_completion(admitted_factory, isolated_factory):
    workflow = admitted_factory(tasks=1)
    workflow.cancel()
    definition = {"id": "manual-values", "requirement_ids": ["R1"],
                  "procedure": "Inspect the displayed approved value.", "expected": "A is 1 and the display is readable."}
    workflow.prepare(manual_checks=[definition])
    workflow.approve()
    initial = run(workflow, scripted_workers([developer(text=FIRST), reviewer()]), isolated_factory)
    workflow.record_manual("manual-values", "passed", "Observed the expected original display.", record_id="manual-before")
    before_feedback = workflow.get()
    original_confirmation = copy.deepcopy(before_feedback["manual_checks"][0])
    assert workflow.acceptance_status()["ready"]
    workflow.feedback("Recheck the reported display issue against the approved behavior.", kind="defect", task_id="T1")
    worker = scripted_workers([developer(), reviewer()])
    final = run(workflow, worker, isolated_factory)
    assert final["stage"] == "technically_complete" and not worker.pending
    assert final["content_version"] == initial["content_version"]
    assert final["execution"]["final_validation_ids"] != initial["execution"]["final_validation_ids"]
    assert completion_id(final) != completion_id(initial)
    assert final["manual_checks"][0] == original_confirmation
    gate = workflow.acceptance_status()
    assert gate["technical_ready"] and not gate["ready"]
    assert gate["manual"][0]["status"] == "stale"
    with pytest.raises(HarnessError, match="Manual check .* stale"):
        workflow.accept()
    workflow.record_manual("manual-values", "passed", "Repeated the check after the new final validation.", record_id="manual-after")
    accepted = workflow.accept()
    assert accepted["stage"] == "accepted"
    assert accepted["acceptance"]["completion_id"] == completion_id(final)
    assert accepted["acceptance"]["manual_check_ids"] == ["manual-after"]
    assert accepted["manual_checks"][0] == original_confirmation
    assert all(item["ended"] is not None for item in accepted["waits"] if item["reason"] == "result_acceptance")


def test_requirements_cli_starts_fresh_planning_and_cannot_reuse_old_authorization(admitted_factory, isolated_factory, tmp_path):
    workflow = admitted_factory(tasks=1)
    worker = scripted_workers([developer(text=FIRST), reviewer()])
    original = run(workflow, worker, isolated_factory)
    original_attempts = copy.deepcopy(original["attempts"])
    original_approval = copy.deepcopy(original["approval"])
    original_plan_id = original["planning_run_id"]
    specification = workflow.project / "spec.md"
    updated_spec = specification.read_text(encoding="utf-8") + "New requirement: display a label with the result.\n"
    specification.write_text(updated_spec, encoding="utf-8")
    feedback_text = "  Change requirements to include a displayed label.\nPreserve this exact request.  "
    feedback_file = tmp_path / "requirements-feedback.txt"
    feedback_file.write_text(feedback_text, encoding="utf-8")
    submitted = call(workflow, "workflow-feedback", "--kind", "requirements", "--from", str(feedback_file),
                     "--feedback-id", "requirements-change")
    assert submitted.returncode == 0, submitted.stdout + submitted.stderr
    report = json.loads(submitted.stdout)
    assert report["stage"] == "replanning_required" and report["feedback"][0]["text"] == feedback_text
    routed = workflow.get()
    assert routed["approval"] == original_approval and routed["attempts"] == original_attempts
    for command in ("workflow-run", "workflow-resume", "workflow-prepare", "workflow-approve"):
        blocked = call(workflow, command)
        assert blocked.returncode != 0, (command, blocked.stdout)
    assert workflow.get() == routed
    replanned = call(workflow, "workflow-replan")
    assert replanned.returncode == 0, replanned.stdout + replanned.stderr
    public = json.loads(replanned.stdout)
    assert public["stage"] == "baseline_pending" and public["approval"] is None
    planner = Planning(workflow.project, workflow.store.home)
    replacement = planner.get()
    assert replacement["id"] != original_plan_id
    assert replacement["baseline"] == content_baseline(workflow.project)
    assert replacement["input_hash"] == digest(replacement["baseline"])
    assert replacement["attempts"] == [] and replacement["baseline_evidence"] == []
    assert replacement["versions"] == [] and replacement["approval"] is None
    assert replacement["feedback_source"]["workflow_run_id"] == original["id"]
    old = workflow.get()
    assert old["stage"] == "superseded"
    assert old["feedback"][0]["text"] == feedback_text and old["feedback"][0]["outcome"] == "replanning_started"
    assert old["approval"] == original_approval and old["attempts"] == original_attempts
    assert specification.read_text(encoding="utf-8") == updated_spec
    for command in ("workflow-run", "workflow-resume", "workflow-prepare", "workflow-approve"):
        blocked = call(workflow, command)
        assert blocked.returncode != 0, (command, blocked.stdout)
    assert planner.replan()["id"] == replacement["id"]
    checked = planner.plan(baseline_only=True, validator_factory=isolated_factory)
    assert checked["stage"] == "planning", checked.get("reason")
    assert checked["approval"] is None and checked["versions"] == []
    assert checked["baseline_evidence"] and all(item["outcome"] == "passed" for item in checked["baseline_evidence"])
    assert all(item["role"] == "baseline_validation" for item in checked["attempts"])
    assert all(item["backend"] == "appcontainer" and item["input_hash"] == checked["input_hash"]
               and item["scope"] == "project_planning" for item in checked["baseline_evidence"])
    assert all(item["process_result"]["token"] == {"appcontainer": True, "capability_count": 0, "elevated": False}
               for item in checked["baseline_evidence"])
    assert planner.status()["actual_ai_call_attempts"] == 0
    assert len(worker.calls) == 2


@pytest.mark.parametrize("failure", ["permission", "failed", "interrupted"])
def test_replanned_baseline_fails_closed_without_host_fallback(admitted_factory, isolated_factory, monkeypatch, failure):
    workflow = admitted_factory(tasks=1)
    run(workflow, scripted_workers([developer(text=FIRST), reviewer()]), isolated_factory)
    workflow.feedback("The next plan needs a changed display requirement.", kind="requirements")
    planner = Planning(workflow.project, workflow.store.home)
    replacement = planner.replan()
    calls = []
    monkeypatch.setattr("development_harness.planning.validate",
                        lambda *args, **kwargs: pytest.fail("Generated replanning baseline cannot use host validation"))

    class FailingIsolatedValidator:
        def __init__(self, directory):
            assert Path(directory).parent == planner.store.home / "replanning-validation"

        def verify(self):
            calls.append("verify")
            if failure == "permission":
                raise PermissionError("Fixture denied isolated permission verification")
            return {"ready": True}

        def run(self, check, project, *, launched, attempt_id):
            calls.append("run")
            started = time.time()
            evidence = {"id": attempt_id, "backend": "appcontainer", "outcome": "running",
                        "started": started, "ended": None, "duration": None, "tests": 0}
            launched(evidence)
            if failure == "interrupted":
                raise KeyboardInterrupt
            return evidence | {"outcome": "failed", "tests": 1, "exit_code": 1, "failure_kind": "code",
                               "ended": started + 1, "duration": 1}

    stopped = planner.plan(baseline_only=True, validator_factory=FailingIsolatedValidator,
                           adapter_factory=lambda *args: pytest.fail("A failed baseline cannot call a Planner"))
    assert stopped["id"] == replacement["id"] and stopped["stage"] == "baseline_pending"
    assert stopped["approval"] is None and stopped["versions"] == [] and stopped["baseline_evidence"] == []
    assert stopped["reason"]
    attempt = stopped["attempts"][0]
    assert attempt["backend"] == "appcontainer" and attempt["role"] == "baseline_validation"
    assert attempt["input_hash"] == stopped["input_hash"] and attempt["scope"] == "project_planning"
    assert attempt["outcome"] == {"permission": "unverified", "failed": "failed", "interrupted": "interrupted"}[failure]
    assert calls == (["verify"] if failure == "permission" else ["verify", "run"])
    if failure in {"permission", "interrupted"}:
        assert attempt["ended"] is None and attempt["duration"] is None
    assert planner.status()["actual_ai_call_attempts"] == 0
