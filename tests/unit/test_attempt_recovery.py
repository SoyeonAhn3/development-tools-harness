"""Local subprocess evidence and recovery decisions; no live AI service calls."""

import copy
import json
from pathlib import Path
import sqlite3
import sys

import pytest

from development_harness.isolated_validation import review_evidence
from development_harness.model import HarnessError, digest, file_digest
from development_harness.store import Store
from development_harness.worker_contract import TaskScope, save_record
from development_harness.workers import CodexWorker
from development_harness.workflow_attempt_recovery import reconcile_attempt
from development_harness.workflow_records import WorkflowRecords, effective_attempt, reconciled_retry


class LocalWorker(CodexWorker):
    """Exercise the real durable-intent transport against a deterministic subprocess."""
    def verify(self):
        self.exe = Path(sys.executable)
        self.policy = {"binary_hash": file_digest(self.exe), "profile": "text-only-v1", "ready": True}
        return self.policy

    def arguments(self, schema=None):
        events = [{"type": "thread.started", "thread_id": "session-" + self.directory.name},
                  {"type": "turn.started"},
                  {"type": "item.completed", "item": {"type": "agent_message", "text": json.dumps(self.response)}},
                  {"type": "turn.completed", "usage": {"input_tokens": 5, "output_tokens": 3}}]
        code = "import sys; sys.stdin.buffer.read(); print(" + repr("\n".join(json.dumps(e) for e in events)) + ")"
        return [sys.executable, "-c", code]


@pytest.fixture
def setup(tmp_path):
    project = tmp_path / "project"
    project.mkdir()
    (project / "code.py").write_text("VALUE = 0\n", encoding="utf-8")
    scope = TaskScope(project, "T1", {"R1": "Set value to one."}, ["code.py"], [])
    store = Store(project, tmp_path / "runtime")
    checks = [{"argv": ["{python}", "-m", "pytest", "-q"], "kind": "pytest", "timeout": 30}]
    policy = {"validation": checks, "worker_boundary": "text-only-v1"}
    store.save({"id": "workflow", "kind": "workflow", "stage": "executing", "expected": scope.baseline,
                "plan_hash": "plan", "policy_hash": digest(policy), "policy": policy,
                "tasks": [{"id": "T1", "requirements": ["R1"], "paths": ["code.py"]}],
                "attempts": [], "findings": {}, "waits": [], "config": {"model": "local-fixture"},
                "execution": {"task_states": {"T1": {"before": scope.files}}}}, "created", new=True)

    class FixtureWorkflow:
        def __init__(self):
            self.project, self.store = project, store

        def get(self):
            return store.get("workflow")

        def _scope(self, run, task_id):
            return scope.refresh()

    workflow = FixtureWorkflow()
    records = WorkflowRecords(store, "workflow")
    return workflow, records, scope


def proposal(scope):
    return {"task_id": "T1", "status": "changes", "summary": "Set the approved value.", "questions": [],
            "changes": [{"path": "code.py", "base_sha256": scope.baseline["code.py"], "content": "VALUE = 1\n"}]}


def launch(setup, *, role="developer", final_failure=True, name="attempt", prior=None, response=None):
    workflow, records, scope = setup
    attempt = records.prepare_attempt("T1", role, digest(scope.baseline), attempt_id=name)
    directory = workflow.store.directory / "workflow/workflow" / name
    worker = LocalWorker(role, "local-fixture", directory)
    worker.response = response or (proposal(scope) if role == "developer" else
                                 {"task_id": "T1", "verdict": "pass", "summary": "Verified", "findings": [], "questions": []})

    def callback(item, phase):
        if final_failure and phase == "finished":
            raise sqlite3.OperationalError("Crash before final journal commit")
        return records.lifecycle(item, phase)

    options = {}
    if role == "reviewer":
        batch = workflow.get()["execution"]["task_states"]["T1"].get("validation_ids", [])
        validations = [review_evidence(item) for item in workflow.get()["attempts"]
                       if item["role"] == "validation" and item["id"] in batch]
        options.update(before=scope.files, validation=validations, prior_findings=prior)
    if final_failure:
        with pytest.raises(sqlite3.OperationalError, match="Crash before final"):
            worker.invoke(scope, attempt=attempt, lifecycle=callback, **options)
    else:
        worker.invoke(scope, attempt=attempt, lifecycle=callback, **options)
    return attempt, directory


def validation(setup, *, name="check", outcome="passed"):
    workflow, records, scope = setup
    check = workflow.get()["policy"]["validation"][0]
    attempt = records.prepare_attempt("T1", "validation", digest(scope.baseline), attempt_id=name)
    attempt.update(check_hash=digest(check), outcome=outcome, tests=1, argv=check["argv"], exit_code=0)
    records.lifecycle(attempt, "finished")
    workflow.store.transition("workflow", "batch-" + name, "test_batch", {},
        lambda run: run["execution"]["task_states"]["T1"].update(validation_ids=[name]))
    return attempt


def test_complete_saved_response_reused_once_without_modifying_original_observations(setup):
    workflow, records, scope = setup
    _, directory = launch(setup)
    original = copy.deepcopy(workflow.get()["attempts"][0])
    assert original["outcome"] == "responded" and "finished" not in original["journal_phases"]
    before = workflow.get()
    preview = reconcile_attempt(workflow, "attempt", commit=False)
    assert workflow.get() == before
    assert preview["action"] == "reuse" and preview["attempt"]["outcome"] == "validated"
    result = reconcile_attempt(workflow, "attempt")
    assert result["response"] == proposal(scope)
    persisted = workflow.get()["attempts"][0]
    assert {key: persisted[key] for key in original} == original
    assert persisted["recovery"]["original_hash"] == digest(original)
    assert set(persisted["recovery"]["evidence"]["artifacts"]) == {
        "attempt.json", "input.json", "response.json", "schema.json", "events.jsonl"}
    events = len(workflow.store.events("workflow"))
    assert reconcile_attempt(workflow, "attempt") == result
    assert len(workflow.store.events("workflow")) == events
    assert records.summary()["total_ai_calls"] == 1
    assert len(workflow.get()["attempts"]) == 1
    assert (scope.project / "code.py").read_text() == "VALUE = 0\n"
    # Recovery does not permit the original worker to append or rewrite history.
    saved = json.loads((directory / "attempt.json").read_text())
    with pytest.raises(HarnessError, match="reconciled attempt"):
        records.lifecycle(saved, "finished")


def test_finished_observations_are_immutable_during_reconciliation(setup):
    workflow, _, _ = setup
    launch(setup, final_failure=False)
    original = copy.deepcopy(workflow.get()["attempts"][0])
    result = reconcile_attempt(workflow, "attempt")
    assert result["action"] == "reuse"
    assert {key: workflow.get()["attempts"][0][key] for key in original} == original


def test_proven_unsent_attempt_is_settled_and_a_fresh_identity_can_be_prepared(setup):
    workflow, records, scope = setup
    original = records.prepare_attempt("T1", "developer", digest(scope.baseline), attempt_id="unsent")
    result = reconcile_attempt(workflow, "unsent")
    assert result["action"] == "retry" and result["response"] is None
    assert reconciled_retry(result["attempt"])
    assert result["attempt"]["actual_ai_call_attempts"] == 0
    assert records.summary()["total_ai_calls"] == 0
    assert {key: workflow.get()["attempts"][0][key] for key in original} == original
    records.prepare_attempt("T1", "developer", digest(scope.baseline), attempt_id="retry")
    assert len(workflow.get()["attempts"]) == 2


def test_failed_durable_dispatch_callback_is_proven_unsent_even_with_local_intent(setup):
    workflow, records, scope = setup
    attempt = records.prepare_attempt("T1", "developer", digest(scope.baseline), attempt_id="unsent")
    worker = LocalWorker("developer", "local-fixture", workflow.store.directory / "workflow/workflow/unsent")
    worker.response = proposal(scope)

    def callback(record, phase):
        if phase == "dispatch_intent":
            raise sqlite3.OperationalError("intent commit failed")
        records.lifecycle(record, phase)

    with pytest.raises(sqlite3.OperationalError, match="intent commit failed"):
        worker.invoke(scope, attempt=attempt, lifecycle=callback)
    raw = workflow.get()["attempts"][0]
    assert raw["dispatch_status"] == "uncertain" and "dispatch_intent" not in raw["journal_phases"]
    result = reconcile_attempt(workflow, "unsent")
    assert result["action"] == "retry"
    assert result["attempt"]["confirmed_ai_calls"] == 0
    assert records.summary()["total_ai_calls"] == 0


def test_sent_attempt_without_saved_complete_response_blocks_without_dispatch(setup):
    workflow, records, scope = setup
    launch(setup)
    directory = workflow.store.directory / "workflow/workflow/attempt"
    (directory / "response.json").unlink()
    before = workflow.get()
    with pytest.raises(HarnessError, match="recovery artifact"):
        reconcile_attempt(workflow, "attempt")
    assert workflow.get() == before
    with pytest.raises(HarnessError, match="unfinished"):
        records.prepare_attempt("T1", "developer", digest(scope.baseline), attempt_id="forbidden")


@pytest.mark.parametrize("artifact,change", [
    ("input.json", lambda value: value.update(instructions="Forged instructions")),
    ("response.json", lambda value: value.update(summary="Different output")),
    ("schema.json", lambda value: value.update(additionalProperties=True)),
    ("attempt.json", lambda value: value.update(id="another-attempt")),
    ("attempt.json", lambda value: value.update(exit_code=1)),
    ("attempt.json", lambda value: value.update(log="C:/outside/events.jsonl")),
    ("attempt.json", lambda value: value.update(session_id="wrong-session")),
    ("attempt.json", lambda value: value.update(usage={"input_tokens": 1000})),
])
def test_changed_artifacts_are_rejected_without_journal_mutation(setup, artifact, change):
    workflow, _, _ = setup
    _, directory = launch(setup)
    value = json.loads((directory / artifact).read_text())
    change(value)
    save_record(directory / artifact, value)
    before = workflow.get()
    with pytest.raises(HarnessError):
        reconcile_attempt(workflow, "attempt")
    assert workflow.get() == before


@pytest.mark.parametrize("corruption", ["truncated", "failed-turn", "tool-event", "duplicate-session"])
def test_incomplete_or_tool_using_transport_is_not_adopted(setup, corruption):
    workflow, _, _ = setup
    _, directory = launch(setup)
    path = directory / "events.jsonl"
    lines = path.read_text().splitlines()
    if corruption == "truncated":
        lines.pop()
    elif corruption == "failed-turn":
        lines.append(json.dumps({"type": "turn.failed"}))
    elif corruption == "tool-event":
        lines.insert(2, json.dumps({"type": "item.completed", "item": {"type": "command_execution"}}))
    else:
        lines.insert(0, lines[0])
    path.write_text("\n".join(lines), encoding="utf-8")
    with pytest.raises(HarnessError):
        reconcile_attempt(workflow, "attempt")
    assert "recovery" not in workflow.get()["attempts"][0]


def test_changed_current_scope_rejects_response_but_explicit_original_scope_supports_partial_patch(setup):
    workflow, _, scope = setup
    launch(setup)
    (scope.project / "code.py").write_text("VALUE = 1\n", encoding="utf-8")
    with pytest.raises(HarnessError, match="original Task scope"):
        reconcile_attempt(workflow, "attempt")
    # Caller has independently proved the actual partial file is exactly before/after.
    assert reconcile_attempt(workflow, "attempt", scope=scope)["action"] == "reuse"


def test_reviewer_response_is_bound_to_before_files_and_latest_passing_validation(setup):
    workflow, records, _ = setup
    check = validation(setup)
    launch(setup, role="reviewer")
    result = reconcile_attempt(workflow, "attempt")
    assert result["attempt"]["review_validation_ids"] == [check["id"]]
    assert not result["attempt"].get("findings_ingested")
    assert records.ingest_findings("attempt", result["response"]["findings"]) == []
    assert reconcile_attempt(workflow, "attempt")["action"] == "reuse"


@pytest.mark.parametrize("mutation", ["before", "validation", "batch", "prior"])
def test_reviewer_recovery_rejects_changed_controller_context(setup, mutation):
    workflow, _, _ = setup
    validation(setup)
    launch(setup, role="reviewer")

    def change(run):
        state = run["execution"]["task_states"]["T1"]
        if mutation == "before":
            state["before"][0]["text"] = "Different beginning"
        elif mutation == "validation":
            run["attempts"][0]["outcome"] = "failed"
        elif mutation == "batch":
            state["validation_ids"] = ["different-check"]
        else:
            run["findings"]["new"] = {"id": "new", "task_id": "T1", "requirement_id": "R1", "path": "code.py",
                "required": True, "status": "open", "severity": "high", "evidence": "Defect", "recommendation": "Fix"}

    workflow.store.transition("workflow", "changed-context", "test", {}, change)
    with pytest.raises(HarnessError, match="Reviewer"):
        reconcile_attempt(workflow, "attempt")


def test_interrupted_validation_is_settled_for_retry_without_inventing_pass_or_duration(setup):
    workflow, records, scope = setup
    attempt = records.prepare_attempt("T1", "validation", digest(scope.baseline), attempt_id="interrupted")
    records.lifecycle(attempt, "prepared")
    before = workflow.get()
    preview = reconcile_attempt(workflow, "interrupted", commit=False)
    assert workflow.get() == before
    assert preview["action"] == "retry"
    result = reconcile_attempt(workflow, "interrupted")
    assert result["attempt"]["outcome"] == "interrupted"
    assert result["attempt"]["duration"] is None
    records.prepare_attempt("T1", "validation", digest(scope.baseline), attempt_id="rerun")


def test_followup_recovery_replays_after_findings_were_already_closed(setup):
    workflow, records, _ = setup
    validation(setup, name="initial-check")
    finding = {"id": "F1", "requirement_id": "R1", "path": "code.py", "severity": "high", "required": True,
               "evidence": "The original assertion was incomplete.", "recommendation": "Verify the complete requirement."}
    initial = {"task_id": "T1", "verdict": "changes", "summary": "Review requires correction.",
               "findings": [finding], "questions": []}
    launch(setup, role="reviewer", name="initial-review", final_failure=False, response=initial)
    observed = records.ingest_findings("initial-review", [finding])
    fields = ("id", "task_id", "requirement_id", "path", "required", "status", "evidence", "recommendation", "severity")
    prior = [{key: item[key] for key in fields} for item in observed]
    validation(setup, name="followup-check")
    followup = {"task_id": "T1", "verdict": "pass", "summary": "Independent evidence closes the finding.",
                "findings": [], "questions": [], "assessments": [{"finding_id": prior[0]["id"], "status": "resolved",
                    "reason": "The registered regression check confirms the requirement.",
                    "evidence": "Current files and the new passing validation cover the original assertion."}]}
    launch(setup, role="reviewer", name="followup", response=followup, prior=prior)
    result = reconcile_attempt(workflow, "followup")
    records.apply_review_assessments("followup", result["response"])
    assert not records.summary()["blocking_findings"]
    before = workflow.get()
    # A controller crash here must reuse the historical input, although current
    # findings are now resolved, and replay the same assessment transaction once.
    again = reconcile_attempt(workflow, "followup")
    records.apply_review_assessments("followup", again["response"])
    assert workflow.get() == before


@pytest.mark.parametrize("commit", [False, True])
def test_invalid_new_recovery_timing_is_rejected_in_preview_and_commit(setup, commit):
    workflow, _, _ = setup
    _, directory = launch(setup)
    saved = json.loads((directory / "attempt.json").read_text())
    saved["finished_at"] = -1
    save_record(directory / "attempt.json", saved)
    with pytest.raises(HarnessError, match="finite nonnegative"):
        reconcile_attempt(workflow, "attempt", commit=commit)


def test_completed_validation_is_never_demoted_for_recovery(setup):
    workflow, _, _ = setup
    validation(setup)
    with pytest.raises(HarnessError, match="Completed validation"):
        reconcile_attempt(workflow, "check")


def test_recovery_event_and_projection_roll_back_atomically(setup):
    workflow, _, _ = setup
    launch(setup)
    before = workflow.get()
    with workflow.store.connect() as db:
        db.executescript("""CREATE TRIGGER fail_recovery BEFORE INSERT ON events
            WHEN NEW.kind = 'workflow_attempt_reconciled'
            BEGIN SELECT RAISE(ABORT, 'interrupted recovery'); END;""")
    with pytest.raises(sqlite3.IntegrityError, match="interrupted recovery"):
        reconcile_attempt(workflow, "attempt")
    assert workflow.get() == before


def test_recovered_artifacts_cannot_change_on_repeated_resume(setup):
    workflow, _, _ = setup
    _, directory = launch(setup)
    reconcile_attempt(workflow, "attempt")
    path = directory / "attempt.json"
    value = json.loads(path.read_text())
    value["unobserved_extra"] = "changed artifact"
    save_record(path, value)
    with pytest.raises(HarnessError, match="differ from the recorded reconciliation"):
        reconcile_attempt(workflow, "attempt")


def test_finished_attempt_existing_observation_cannot_be_overwritten_by_recovery(setup):
    _, records, scope = setup
    attempt = records.prepare_attempt("T1", "developer", digest(scope.baseline), attempt_id="conflict")
    records.lifecycle({**attempt, "started": 10}, "prepared")
    with pytest.raises(HarnessError, match="replace an existing observation"):
        records.recover_attempt("conflict", disposition="validated", evidence={}, observations={
            "input_hash": "input", "response_hash": "output", "session_id": "session", "started": 11})
