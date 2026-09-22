"""Result-feedback routing uses an approved fixture without external AI calls."""

import copy
import sqlite3

import pytest

from development_harness.model import HarnessError, digest
from development_harness.workflow import Workflow
from development_harness.workflow_feedback import MAX_FEEDBACK_BYTES, complete_feedback, submit_feedback
from test_planning import StubAdapter, example_plan, fast_baseline, planning_workspace, ready


@pytest.fixture
def completed(planning_workspace, fast_baseline):
    planner, config = planning_workspace
    plan = example_plan()
    second = copy.deepcopy(plan["tasks"][0])
    second.update(id="T2", depends_on=["T1"])
    plan["tasks"].append(second)
    StubAdapter.response = plan
    ready(planner, config)
    planner.approve()
    workflow = Workflow(planner.project, planner.store.home)
    workflow.prepare()
    workflow.approve()
    admitted = workflow.get()
    before = workflow._scope(admitted, "T1").files

    def fixture_result(run):
        run.update(stage="technically_complete", reason=None)
        run["execution"] = {"sequence": 20, "task_index": 2, "stage": "complete", "in_flight": False,
            "active_step": None, "patch_pending": None, "patches": [], "corrections": {"T1": 0, "T2": 1},
            "completed_tasks": ["T1", "T2"], "final_validation_ids": ["original-final"],
            "final_content_version": run["content_version"], "stop_kind": None, "started": 10, "ended": 20,
            "task_states": {identity: {"before": copy.deepcopy(before), "before_content_version": run["content_version"],
                "validation_ids": ["original-check-" + identity], "developer_attempt_id": "original-dev-" + identity,
                "reviewer_attempt_id": "original-review-" + identity, "completed_content_version": run["content_version"],
                "feedback": None} for identity in ("T1", "T2")}}
        run["attempts"] = [{"id": "original-review-" + identity, "task_id": identity, "role": "reviewer",
            "plan_hash": run["plan_hash"], "policy_hash": run["policy_hash"], "content_version": run["content_version"],
            "journal_phases": {"finished": 19}, "outcome": "validated", "review_verdict": "pass",
            "dispatch_status": "responded", "findings_ingested": True, "finding_ids": []} for identity in ("T1", "T2")]
        run["reuse_evidence"] = [{"fixture": "prior reuse attestation"}]
        run["manual_evidence"] = [{"fixture": "prior manual attestation"}]
        run["waits"].append({"id": "result-wait", "reason": "result_acceptance", "started": 20,
                             "ended": None, "duration": None})

    workflow.store.transition(admitted["id"], "fixture-complete", "test_fixture", {}, fixture_result)
    return workflow


def changed(workflow, identity, update):
    return workflow.store.transition(workflow.get()["id"], identity, "test_fixture", {}, update)


def finish_feedback(workflow, *, fresh_review=True):
    def finish(run):
        state = run["execution"]
        state.update(stage="complete", task_index=2, completed_tasks=["T1", "T2"],
                     final_validation_ids=["new-final"], final_content_version=run["content_version"], ended=30)
        if fresh_review:
            for identity in ("T1", "T2"):
                review = {"id": "new-review-" + identity, "task_id": identity, "role": "reviewer",
                    "content_version": run["content_version"], "journal_phases": {"finished": 29},
                    "outcome": "validated", "review_verdict": "pass", "findings_ingested": True}
                run["attempts"].append(review)
                state["task_states"][identity].update(reviewer_attempt_id=review["id"],
                                                     completed_content_version=run["content_version"])
        state["sequence"] += 1
        run["stage"] = "technically_complete"
        complete_feedback(run)
    return changed(workflow, "finish-feedback", finish)


def test_defect_retains_original_feedback_approval_history_and_bounded_counters(completed):
    original = completed.get()
    text = "  Negative input still produces a number.\nPlease verify the approved rejection rule.  "
    result = submit_feedback(completed, text, kind="defect", task_id="T1")
    feedback = result["feedback"][0]
    assert feedback["text"] == text and feedback["outcome"] == "correction_requested"
    assert feedback["plan_hash"] == original["plan_hash"]
    assert feedback["content_version"] == original["content_version"]
    assert feedback["previous_completion"]["final_validation_ids"] == ["original-final"]
    assert feedback["previous_completion"]["task_states"]["T1"]["reviewer_attempt_id"] == "original-review-T1"
    assert result["approval"] == original["approval"]
    assert result["attempts"] == original["attempts"] and result["findings"] == original["findings"]
    assert result["expected"] == original["expected"] and result["policy"] == original["policy"]
    assert result["stage"] == "executing"
    state = result["execution"]
    assert state["corrections"] == {"T1": 1, "T2": 1}
    assert state["task_index"] == 0 and state["completed_tasks"] == [] and state["stage"] == "developer"
    assert state["feedback_rechecks"] == ["T2"]
    assert state["task_states"]["T1"]["before"] == original["execution"]["task_states"]["T1"]["before"]
    assert state["task_states"]["T1"]["feedback"]["evidence"][0]["text"] == text
    assert state["final_validation_ids"] == [] and "final_content_version" not in state
    assert result["reuse_evidence"] == original["reuse_evidence"]
    assert result["manual_evidence"] == original["manual_evidence"]
    wait = next(item for item in result["waits"] if item["id"] == "result-wait")
    assert wait["ended"] == feedback["received_at"] and wait["duration"] == wait["ended"] - 20


def test_later_task_feedback_preserves_completed_predecessors(completed):
    result = submit_feedback(completed, "The second task has a defect.", kind="defect", task_id="T2")
    assert result["execution"]["task_index"] == 1
    assert result["execution"]["completed_tasks"] == ["T1"]
    assert result["execution"]["feedback_rechecks"] == []
    assert result["execution"]["corrections"] == {"T1": 0, "T2": 2}


@pytest.mark.parametrize("explicit", [False, True])
def test_repeated_feedback_is_idempotent_after_routing_changed_the_cursor(completed, explicit):
    options = {"feedback_id": "user-feedback"} if explicit else {}
    first = submit_feedback(completed, "Same original defect", kind="defect", task_id="T1", **options)
    events = len(completed.store.events(first["id"]))
    assert submit_feedback(completed, "Same original defect", kind="defect", task_id="T1", **options) == first
    assert len(completed.store.events(first["id"])) == events


def test_explicit_feedback_identity_cannot_be_reused_with_different_text(completed):
    submit_feedback(completed, "Original text", kind="defect", task_id="T1", feedback_id="stable")
    before = completed.get()
    with pytest.raises(HarnessError, match="different original text"):
        submit_feedback(completed, "Changed text", kind="defect", task_id="T1", feedback_id="stable")
    assert completed.get() == before


def test_requirements_feedback_invalidates_execution_without_losing_approval_or_writing_files(completed):
    original = completed.get()
    content = (completed.project / "value.py").read_bytes()
    result = submit_feedback(completed, "Change the required output format.", kind="requirements")
    assert result["stage"] == "replanning_required"
    assert result["feedback"][0]["outcome"] == "replanning_required"
    assert result["replanning_feedback_id"] == result["feedback"][0]["id"]
    assert result["approval"] == original["approval"]
    assert result["execution"]["corrections"] == original["execution"]["corrections"]
    assert result["attempts"] == original["attempts"]
    wait = next(item for item in result["waits"] if item["id"] == "result-wait")
    assert wait["ended"] == result["feedback"][0]["received_at"]
    assert (completed.project / "value.py").read_bytes() == content


def test_requirements_route_accepts_changed_specification_but_defect_route_preserves_and_blocks_it(completed):
    path = completed.project / "spec.md"
    path.write_text("Changed specification: display a labeled result.\n", encoding="utf-8")
    before = completed.get()
    with pytest.raises(HarnessError, match="Unexpected file changes"):
        submit_feedback(completed, "Fix the output", kind="defect", task_id="T1")
    assert completed.get() == before
    assert submit_feedback(completed, "Specification now requires labels", kind="requirements")["stage"] == "replanning_required"
    assert path.read_text() == "Changed specification: display a labeled result.\n"


def test_exhausted_correction_allowance_preserves_feedback_and_cannot_be_reset(completed):
    changed(completed, "spent-limit", lambda run: run["execution"]["corrections"].update(T1=2))
    before = completed.get()
    result = submit_feedback(completed, "Defect remains after all attempts.", kind="defect", task_id="T1")
    assert result["feedback"][0]["outcome"] == "correction_limit"
    assert result["feedback"][0]["text"] == "Defect remains after all attempts."
    assert result["stage"] == "failed" and result["execution"]["corrections"]["T1"] == 2
    assert result["approval"] == before["approval"] and result["attempts"] == before["attempts"]
    assert submit_feedback(completed, "Defect remains after all attempts.", kind="defect", task_id="T1") == result


@pytest.mark.parametrize("stage,kind", [("failed", "final_code"), ("failed", "code"), ("stopped", "code")])
def test_settled_code_failure_can_receive_scoped_feedback(completed, stage, kind):
    def stop(run):
        run["stage"] = stage
        run["execution"]["stop_kind"] = kind
    changed(completed, "code-failure", stop)
    result = submit_feedback(completed, "Fix this approved behavior.", kind="defect", task_id="T1")
    assert result["stage"] == "executing"


@pytest.mark.parametrize("kind", ["permission", "environment", "specification", "interrupted", "execution_error"])
def test_non_code_stops_are_not_reclassified_as_defects(completed, kind):
    def stop(run):
        run["stage"] = "stopped"
        run["execution"]["stop_kind"] = kind
    changed(completed, "non-code-failure", stop)
    before = completed.get()
    with pytest.raises(HarnessError, match="cannot be relabeled"):
        submit_feedback(completed, "Try fixing code anyway", kind="defect", task_id="T1")
    assert completed.get() == before


@pytest.mark.parametrize("stage", ["accepted", "cancelled", "superseded"])
def test_finalized_runs_are_never_reopened(completed, stage):
    changed(completed, "terminal", lambda run: run.update(stage=stage))
    before = completed.get()
    with pytest.raises(HarnessError, match="cannot be reopened"):
        submit_feedback(completed, "New request", kind="defect", task_id="T1")
    assert completed.get() == before


@pytest.mark.parametrize("defect", ["in_flight", "partial", "pending", "alive"])
def test_unsafe_execution_cannot_be_bypassed_by_feedback(completed, monkeypatch, defect):
    if defect == "in_flight":
        changed(completed, "busy", lambda run: run["execution"].update(in_flight=True))
    elif defect == "partial":
        changed(completed, "partial", lambda run: run["execution"].update(patch_pending={"attempt_id": "partial"}))
    elif defect == "pending":
        monkeypatch.setattr(completed, "_pending", lambda run: ["uncertain"])
    else:
        def refuse(attempts):
            raise HarnessError("A recorded process is still active")
        monkeypatch.setattr("development_harness.workflow_feedback.ensure_stopped", refuse)
    before = completed.get()
    with pytest.raises(HarnessError, match="Recover incomplete|still active"):
        submit_feedback(completed, "Change requirements", kind="requirements")
    assert completed.get() == before


@pytest.mark.parametrize("text,kind,task", [("", "defect", "T1"), (" ", "defect", "T1"),
    ("x" * (MAX_FEEDBACK_BYTES + 1), "defect", "T1"), ("broken\0text", "defect", "T1"),
    ("Fix", "unknown", "T1"), ("Fix", "defect", None), ("Fix", "defect", "outside")])
def test_invalid_feedback_is_rejected_without_mutation(completed, text, kind, task):
    before = completed.get()
    with pytest.raises(HarnessError):
        submit_feedback(completed, text, kind=kind, task_id=task)
    assert completed.get() == before


def test_feedback_and_execution_transition_roll_back_together(completed):
    before = completed.get()
    with completed.store.connect() as db:
        db.executescript("""CREATE TRIGGER fail_feedback BEFORE INSERT ON events
            WHEN NEW.kind = 'workflow_feedback_routed'
            BEGIN SELECT RAISE(ABORT, 'feedback commit failed'); END;""")
    with pytest.raises(sqlite3.IntegrityError, match="feedback commit failed"):
        submit_feedback(completed, "Original feedback", kind="defect", task_id="T1")
    assert completed.get() == before


def test_completed_correction_keeps_original_feedback_and_binds_new_evidence(completed):
    submitted = submit_feedback(completed, "Original feedback", kind="defect", task_id="T1")
    original = submitted["feedback"][0]
    result = finish_feedback(completed)
    feedback = result["feedback"][0]
    assert feedback["text"] == original["text"]
    assert feedback["routing_outcome"] == "correction_requested"
    assert feedback["outcome"] == "corrected"
    assert feedback["previous_completion"] == original["previous_completion"]
    assert feedback["resolution"]["reviewer_attempt_id"] == "new-review-T1"
    assert feedback["resolution"]["final_validation_ids"] == ["new-final"]
    assert [item["outcome"] for item in feedback["history"]] == ["correction_requested", "corrected"]
    copied = copy.deepcopy(result)
    complete_feedback(copied)
    assert copied == result


def test_feedback_cannot_be_closed_with_the_pre_feedback_reviewer(completed):
    submit_feedback(completed, "Still broken", kind="defect", task_id="T1")
    before = completed.get()
    with pytest.raises(HarnessError, match="subsequent independent Reviewer"):
        finish_feedback(completed, fresh_review=False)
    assert completed.get() == before


def test_identical_feedback_after_a_new_completion_is_a_new_bounded_request(completed):
    first = submit_feedback(completed, "Still broken", kind="defect", task_id="T1")
    finish_feedback(completed)
    second = submit_feedback(completed, "Still broken", kind="defect", task_id="T1")
    assert len(second["feedback"]) == 2
    assert second["feedback"][0]["id"] == first["feedback"][0]["id"]
    assert second["feedback"][1]["id"] != first["feedback"][0]["id"]
    assert second["execution"]["corrections"]["T1"] == 2
