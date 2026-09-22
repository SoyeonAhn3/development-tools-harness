"""Regression cases found during the independent T3 admission review."""

import pytest

from development_harness.model import HarnessError, digest
from development_harness.planning import Planning
from development_harness.workflow_records import WorkflowRecords
from test_planning import fast_baseline, planning_workspace
from test_workflow_admission import approved


@pytest.mark.parametrize("name", ["value.py", "late-user-file.txt"])
def test_change_after_initial_planning_check_cannot_be_admitted(approved, monkeypatch, name):
    planner, source, workflow = approved
    original = Planning._check

    def changed_after_check(controller, run):
        files = original(controller, run)
        (controller.project / name).write_text("user edit after the initial baseline check\n")
        return files

    monkeypatch.setattr(Planning, "_check", changed_after_check)
    with pytest.raises(HarnessError, match="approved planning baseline"):
        workflow.prepare()
    assert workflow.store.get()["id"] == source["id"]
    assert workflow.store.active() is None
    assert (planner.project / name).read_text() == "user edit after the initial baseline check\n"


def test_cancelled_authorization_is_reported_as_inactive(approved):
    _, _, workflow = approved
    workflow.prepare()
    approval = workflow.approve()["approval"]
    workflow.cancel()
    result = workflow.status()
    assert result["approval"] == approval  # Preserve the historical decision.
    assert result["execution_authorized"] is False


def test_backwards_wall_clock_does_not_invent_zero_approval_wait(approved, monkeypatch):
    _, _, workflow = approved
    prepared = workflow.prepare()
    started = prepared["waits"][0]["started"]
    monkeypatch.setattr("development_harness.workflow.time.time", lambda: started - 5)
    workflow.approve()
    result = workflow.status()
    assert result["waits"][0]["ended"] == started - 5
    assert result["waits"][0]["duration"] is None
    assert result["approval_wait"] is None


def test_review_completed_before_findings_ingestion_blocks_further_dispatch(approved):
    _, _, workflow = approved
    workflow.prepare()
    run = workflow.approve()
    records = WorkflowRecords(workflow.store, run["id"])
    attempt = records.prepare_attempt("T1", "reviewer", run["content_version"])
    for index, phase in enumerate(("prepared", "process_registered", "dispatch_intent", "responded", "finished")):
        attempt[phase + "_at"] = index + 1
        if phase == "responded":
            attempt["response_hash"] = digest({"verdict": "pass", "findings": []})
        if phase == "finished":
            attempt.update(outcome="validated", review_verdict="pass", review_findings_hash=digest([]))
        records.lifecycle(attempt, phase)
    result = workflow.status()
    assert result["pending_review_attempts"] == [attempt["id"]]
    assert result["pending_record_attempts"] == [attempt["id"]]
    with pytest.raises(HarnessError, match="inspection"):
        workflow.invoke("T1", "developer", worker_factory=lambda *args: pytest.fail("No new AI dispatch"))
    with pytest.raises(HarnessError, match="inspection"):
        workflow.validate_task("T1", 0, validator_factory=lambda *args: pytest.fail("No new validation dispatch"))
    records.ingest_findings(attempt["id"], [])
    assert workflow.status()["pending_review_attempts"] == []
    assert workflow.status()["pending_record_attempts"] == []
