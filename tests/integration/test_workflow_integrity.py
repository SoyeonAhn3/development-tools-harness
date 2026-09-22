"""Durable T4 boundary continuation and rejection of untracked file changes.

Worker transport is a real local subprocess fixture. Validation is recorded
passing evidence here; actual isolated validation is covered in test_workflow.
"""

import copy
import json
from pathlib import Path

import pytest

from development_harness.files import snapshot
from development_harness.model import HarnessError, digest, file_digest
from development_harness.workflow import Workflow
from development_harness.workflow_records import WorkflowRecords
from test_workflow import FIRST, FINAL, admitted_factory, developer, reviewer, scripted_workers


class PassingValidator:
    def __init__(self, directory):
        pass

    def verify(self):
        return {"ready": True, "test_fixture": True}

    def run(self, check, project, *, launched, attempt_id):
        evidence = {"id": attempt_id, "content_version": digest(snapshot(project)),
                    "check_hash": digest(check), "argv": check["argv"], "outcome": "running",
                    "started": 100.0, "ended": None, "duration": None, "tests": 0}
        launched(evidence)
        return evidence | {"outcome": "passed", "ended": 101.0, "duration": 1.0,
                           "tests": 1, "exit_code": 0}


@pytest.fixture
def paused_workflow(admitted_factory):
    workflow = admitted_factory(tasks=1)
    worker = scripted_workers([developer(text=FIRST), reviewer()])
    run = workflow.execute(worker_factory=worker, validator_factory=PassingValidator, steps=1)
    assert run["stage"] == "executing", run.get("reason")
    assert run["execution"]["stage"] == "validation"
    assert run["execution"]["in_flight"] is False
    assert len(run["attempts"]) == len(run["execution"]["patches"]) == 1
    return workflow, worker


def test_new_controller_continues_each_completed_boundary_without_replaying(admitted_factory):
    workflow = admitted_factory()
    worker = scripted_workers([developer(text=FIRST), reviewer(), developer("T2", FINAL), reviewer("T2")])
    initial = workflow.get()
    seen_attempts, seen_patches = [], []
    next_stages = ["validation", "review", "developer", "validation", "review", "final_validation", "complete"]
    for index, next_stage in enumerate(next_stages):
        # Reconstruct the controller exactly as separate CLI invocations do.
        workflow = Workflow(workflow.project, workflow.store.home)
        run = workflow.execute(worker_factory=worker, validator_factory=PassingValidator, steps=1)
        assert run["execution"]["stage"] == next_stage, run.get("reason")
        assert run["execution"]["in_flight"] is False
        assert run["execution"]["patch_pending"] is None
        assert run["approval"] == initial["approval"]
        attempt_ids = [attempt["id"] for attempt in run["attempts"]]
        assert attempt_ids[:len(seen_attempts)] == seen_attempts
        assert len(attempt_ids) == len(seen_attempts) + 1 == index + 1
        assert len(set(attempt_ids)) == len(attempt_ids)
        patch_ids = [patch["attempt_id"] for patch in run["execution"]["patches"]]
        assert patch_ids[:len(seen_patches)] == seen_patches
        seen_attempts, seen_patches = attempt_ids, patch_ids
        assert "inspection_error" not in workflow.status()
    assert run["stage"] == "technically_complete"
    assert run["execution"]["completed_tasks"] == ["T1", "T2"]
    assert len(seen_patches) == 2
    assert len(worker.calls) == 4 and not worker.pending
    assert (workflow.project / "value.py").read_text(encoding="utf-8") == FINAL
    events = workflow.store.events(run["id"])
    assert workflow.execute(worker_factory=worker, validator_factory=PassingValidator) == run
    assert workflow.store.events(run["id"]) == events


@pytest.mark.parametrize("tampering", ["raw_bytes", "proposal", "record_location"])
def test_modified_patch_evidence_cannot_authorize_the_next_boundary(paused_workflow, tampering, tmp_path):
    workflow, worker = paused_workflow
    run = workflow.get()
    patch = run["execution"]["patches"][0]
    record = Path(patch["record"])
    if tampering == "raw_bytes":
        record.write_bytes(record.read_bytes() + b"\n")
        message = "patch evidence changed"
    elif tampering == "proposal":
        value = json.loads(record.read_text(encoding="utf-8"))
        value["proposal"]["changes"][0]["content"] = "A = 999\nB = 0\n"
        record.write_text(json.dumps(value), encoding="utf-8", newline="\n")
        patch["record_hash"] = file_digest(record)
        workflow.store.save(run, "test_patch_metadata_tampered")
        message = "recorded Developer proposal"
    else:
        replacement = tmp_path / "substituted-patch.json"
        replacement.write_bytes(record.read_bytes())
        patch["record"] = str(replacement)
        workflow.store.save(run, "test_patch_location_tampered")
        message = "outside its recorded attempt directory"
    before = snapshot(workflow.project)
    attempts = copy.deepcopy(workflow.get()["attempts"])
    with pytest.raises(HarnessError, match=message):
        workflow.execute(worker_factory=worker, validator_factory=PassingValidator)
    assert workflow.get()["attempts"] == attempts
    assert len(worker.calls) == 1 and len(worker.pending) == 1
    assert snapshot(workflow.project) == before
    assert message in workflow.status()["inspection_error"]


def test_forging_current_snapshot_does_not_adopt_an_unrecorded_user_edit(paused_workflow):
    workflow, worker = paused_workflow
    user_text = "A = 47\nB = 91\n# User work must remain intact.\n"
    (workflow.project / "value.py").write_text(user_text, encoding="utf-8", newline="\n")
    run = workflow.get()
    run["expected"] = snapshot(workflow.project)
    run["content_version"] = digest(run["expected"])
    workflow.store.save(run, "test_adopted_unrecorded_snapshot")
    with pytest.raises(HarnessError, match="complete chain of recorded patches"):
        workflow.execute(worker_factory=worker, validator_factory=PassingValidator)
    assert (workflow.project / "value.py").read_text(encoding="utf-8") == user_text
    assert workflow.get()["attempts"] == run["attempts"]
    assert len(worker.calls) == 1 and len(worker.pending) == 1
    assert "complete chain of recorded patches" in workflow.status()["inspection_error"]


@pytest.mark.parametrize("unfinished", ["in_flight", "patch_pending", "prepared_attempt"])
def test_incomplete_boundary_stops_without_redispatch_or_automatic_recovery(paused_workflow, unfinished):
    workflow, worker = paused_workflow
    run = workflow.get()
    if unfinished == "prepared_attempt":
        WorkflowRecords(workflow.store, run["id"]).prepare_attempt("T1", "developer", run["content_version"])
    else:
        run["execution"][unfinished] = True if unfinished == "in_flight" else {
            "task_id": "T1", "attempt_id": run["attempts"][0]["id"], "before": run["content_version"]}
        workflow.store.save(run, "test_interrupted_boundary")
    attempts = copy.deepcopy(workflow.get()["attempts"])
    before = snapshot(workflow.project)
    result = workflow.execute(worker_factory=worker, validator_factory=PassingValidator)
    assert result["stage"] == "stopped"
    assert result["execution"]["stop_kind"] == "interrupted"
    assert result["execution"]["corrections"] == {"T1": 0}
    assert result["execution"]["completed_tasks"] == []
    assert result["attempts"] == attempts
    assert len(worker.calls) == 1 and len(worker.pending) == 1
    assert snapshot(workflow.project) == before
    events = workflow.store.events(run["id"])
    assert workflow.execute(worker_factory=worker, validator_factory=PassingValidator) == result
    assert workflow.store.events(run["id"]) == events
