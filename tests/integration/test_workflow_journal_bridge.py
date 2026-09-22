"""Real local subprocess -> worker -> SQLite bridge, without an AI service."""

import copy
import json
from pathlib import Path
import sqlite3
import subprocess
import sys

import pytest

from development_harness.files import snapshot
from development_harness.model import HarnessError, digest, file_digest
from development_harness.workers import CodexWorker
from development_harness.workflow import Workflow
from development_harness.workflow_records import WorkflowRecords
from test_workflow_admission_cli import reviewed_planning


class LocalWorker(CodexWorker):
    """Real process transport with deterministic local role response; not AI evidence."""
    def verify(self):
        self.exe = Path(sys.executable)
        self.policy = {"binary_hash": file_digest(self.exe), "profile": "text-only-v1", "test_transport": True}
        return self.policy

    def arguments(self, schema=None):
        response = ({"task_id": "T1", "status": "unchanged", "summary": "Fixture response",
                     "changes": [], "questions": []} if self.role == "developer" else
                    {"task_id": "T1", "verdict": "pass", "summary": "Fixture response",
                     "findings": [], "questions": []})
        events = [{"type": "thread.started", "thread_id": "local-" + self.role},
                  {"type": "turn.started"},
                  {"type": "item.completed", "item": {"type": "agent_message", "text": json.dumps(response)}},
                  {"type": "turn.completed"}]
        code = "import sys,json; sys.stdin.buffer.read(); print(" + repr("\n".join(json.dumps(e) for e in events)) + ")"
        return [sys.executable, "-c", code]


class RecordedValidator:
    """Use actual AppContainer tests elsewhere; isolate journal/controller behavior here."""
    def __init__(self, directory):
        self.directory = directory

    def verify(self):
        return {"ready": True}

    def run(self, check, project, *, launched, attempt_id):
        evidence = {"id": attempt_id, "content_version": digest(snapshot(project)),
                    "check_hash": digest(check), "argv": check["argv"], "outcome": "running",
                    "started": 100.0, "ended": None, "duration": None, "tests": 0}
        launched(evidence)
        return evidence | {"outcome": "passed", "ended": 101.0, "duration": 1.0, "tests": 1, "exit_code": 0}


@pytest.fixture
def admitted(reviewed_planning):
    planner = reviewed_planning
    planner.approve()
    workflow = Workflow(planner.project, planner.store.home)
    workflow.prepare()
    workflow.approve()
    return workflow


def test_real_process_lifecycle_reaches_durable_journal_without_file_changes(admitted):
    before = snapshot(admitted.project)
    result = admitted.invoke("T1", "developer", worker_factory=LocalWorker)
    status = admitted.status()
    attempt = status["attempts"][0]
    assert attempt["id"] == result["attempt"]["id"]
    assert attempt["outcome"] == "validated"
    assert attempt["session_id"] == "local-developer"
    assert set(attempt["journal_phases"]) == {"prepared", "process_registered", "dispatch_intent", "responded", "finished"}
    assert attempt["process"]["pid"] > 0
    assert attempt["plan_hash"] == status["plan_hash"]
    assert attempt["usage"] is None
    assert snapshot(admitted.project) == before
    assert status["orchestration_available"] is True
    persisted = json.loads(Path(attempt["log"]).with_name("attempt.json").read_text(encoding="utf-8"))
    records = WorkflowRecords(admitted.store, status["id"])
    count = len(admitted.store.events(status["id"]))
    records.lifecycle(persisted, "finished")
    assert len(admitted.store.events(status["id"])) == count
    assert len(admitted.get()["attempts"]) == 1


def test_validation_and_reviewer_use_controller_evidence(admitted):
    validation = admitted.validate_task("T1", 0, validator_factory=RecordedValidator)
    result = admitted.invoke("T1", "reviewer", worker_factory=LocalWorker)
    reviewer = admitted.get()["attempts"][-1]
    assert result["response"]["verdict"] == "pass"
    assert reviewer["review_validation_ids"] == [validation["id"]]
    assert reviewer["findings_ingested"] is True
    assert reviewer["finding_ids"] == []
    assert admitted.status()["blocking_findings"] == []


def test_reviewer_rejects_unrecorded_or_forged_validation(admitted):
    with pytest.raises(HarnessError, match="recorded passing"):
        admitted.invoke("T1", "reviewer", worker_factory=LocalWorker)
    assert admitted.get()["attempts"] == []
    admitted.validate_task("T1", 0, validator_factory=RecordedValidator)
    with pytest.raises(HarnessError, match="recorded validation"):
        admitted.invoke("T1", "reviewer", validation=[{"outcome": "passed"}], worker_factory=LocalWorker)
    assert len(admitted.get()["attempts"]) == 1


def test_reviewer_cannot_replace_latest_failure_with_an_older_pass(admitted):
    class FailedValidator(RecordedValidator):
        def run(self, *args, **kwargs):
            return super().run(*args, **kwargs) | {"outcome": "failed", "exit_code": 1, "failure_kind": "code"}

    passed = admitted.validate_task("T1", 0, validator_factory=RecordedValidator)
    failed = admitted.validate_task("T1", 0, validator_factory=FailedValidator)
    assert passed["content_version"] == failed["content_version"]
    assert passed["check_hash"] == failed["check_hash"]
    before = admitted.get()
    with pytest.raises(HarnessError, match="recorded passing"):
        admitted.invoke("T1", "reviewer", worker_factory=lambda *args: pytest.fail("Stale pass cannot dispatch a Reviewer"))
    assert admitted.get() == before


@pytest.mark.parametrize("phase", ["process_registered", "dispatch_intent"])
def test_journal_failure_before_transmission_prevents_input(admitted, monkeypatch, phase):
    original = admitted.store.transition
    def fail(run_id, event_id, kind, detail, update):
        if kind == "workflow_attempt_" + phase:
            raise sqlite3.OperationalError("injected durable write failure")
        return original(run_id, event_id, kind, detail, update)
    monkeypatch.setattr(admitted.store, "transition", fail)
    with pytest.raises(sqlite3.OperationalError, match="injected"):
        admitted.invoke("T1", "developer", worker_factory=LocalWorker)
    attempt = admitted.get()["attempts"][0]
    assert attempt["outcome"] == "unverified"
    assert not Path(attempt["log"]).read_text(encoding="utf-8").strip()
    with pytest.raises(HarnessError, match="inspection"):
        admitted.invoke("T1", "developer", worker_factory=LocalWorker)


def test_final_db_failure_preserves_response_artifact_for_explicit_replay(admitted, monkeypatch):
    original = admitted.store.transition
    def fail(run_id, event_id, kind, detail, update):
        if kind == "workflow_attempt_finished":
            raise sqlite3.OperationalError("final journal failure")
        return original(run_id, event_id, kind, detail, update)
    monkeypatch.setattr(admitted.store, "transition", fail)
    with pytest.raises(sqlite3.OperationalError, match="final journal"):
        admitted.invoke("T1", "developer", worker_factory=LocalWorker)
    run = admitted.get()
    attempt = run["attempts"][0]
    assert attempt["outcome"] == "responded"
    assert "finished" not in attempt["journal_phases"]
    with pytest.raises(HarnessError, match="inspection"):
        admitted.invoke("T1", "developer", worker_factory=LocalWorker)
    directory = Path(attempt["log"]).parent
    raw = json.loads((directory / "attempt.json").read_text(encoding="utf-8"))
    response = json.loads((directory / "response.json").read_text(encoding="utf-8"))
    assert digest(response) == raw["response_hash"]
    monkeypatch.setattr(admitted.store, "transition", original)
    records = WorkflowRecords(admitted.store, run["id"])
    records.lifecycle(raw, "finished")
    records.lifecycle(raw, "finished")
    assert len(admitted.get()["attempts"]) == 1
    assert admitted.get()["attempts"][0]["outcome"] == "validated"


def test_store_transaction_rolls_back_state_when_event_insert_fails(admitted):
    run = admitted.get()
    before = copy.deepcopy(run)
    with admitted.store.connect() as db:
        db.execute("CREATE TRIGGER break_event BEFORE INSERT ON events BEGIN SELECT RAISE(ABORT, 'crash'); END")
    with pytest.raises(sqlite3.IntegrityError, match="crash"):
        admitted.store.transition(run["id"], "stable-transition", "test", {}, lambda value: value.update(reason="must roll back"))
    assert admitted.get() == before
    with admitted.store.connect() as db:
        db.execute("DROP TRIGGER break_event")
    admitted.store.transition(run["id"], "stable-transition", "test", {}, lambda value: value.update(reason="once"))
    admitted.store.transition(run["id"], "stable-transition", "test", {}, lambda value: value.update(reason="twice"))
    assert admitted.get()["reason"] == "once"
    with pytest.raises(HarnessError, match="reused"):
        admitted.store.transition(run["id"], "stable-transition", "test", {"changed": True}, lambda value: None)


def test_controller_process_death_during_sqlite_transition_rolls_back(admitted):
    before = admitted.get()
    code = '''
from contextlib import contextmanager
import os, sys
from development_harness.store import Store
store = Store(sys.argv[1], sys.argv[2])
original = store.connect
@contextmanager
def interrupted_connection():
    with original() as db:
        db.create_function('terminate_controller', 0, lambda: os._exit(73))
        db.execute("CREATE TEMP TRIGGER crash_before_event BEFORE INSERT ON events BEGIN SELECT terminate_controller(); END")
        yield db
store.connect = interrupted_connection
store.transition(sys.argv[3], 'killed-controller', 'crash-test', {}, lambda run: run.update(reason='uncommitted'))
'''
    result = subprocess.run([sys.executable, "-c", code, str(admitted.project),
                             str(admitted.store.home), before["id"]], capture_output=True,
                            timeout=20, creationflags=subprocess.CREATE_NO_WINDOW)
    assert result.returncode == 73, result.stderr
    assert admitted.get() == before
    assert not any(event["id"] == "killed-controller" for event in admitted.store.events(before["id"]))


def test_review_ingestion_failure_blocks_new_calls_and_is_visible(admitted, monkeypatch):
    admitted.validate_task("T1", 0, validator_factory=RecordedValidator)
    original = WorkflowRecords.ingest_findings
    def fail(*args, **kwargs):
        raise sqlite3.OperationalError("review ingestion crash")
    monkeypatch.setattr(WorkflowRecords, "ingest_findings", fail)
    with pytest.raises(sqlite3.OperationalError, match="ingestion"):
        admitted.invoke("T1", "reviewer", worker_factory=LocalWorker)
    reviewer = admitted.get()["attempts"][-1]
    assert reviewer["outcome"] == "validated"
    assert admitted.status()["pending_review_attempts"] == [reviewer["id"]]
    with pytest.raises(HarnessError, match="inspection"):
        admitted.invoke("T1", "developer", worker_factory=LocalWorker)
    with pytest.raises(HarnessError, match="inspection"):
        admitted.validate_task("T1", 0, validator_factory=RecordedValidator)
    monkeypatch.setattr(WorkflowRecords, "ingest_findings", original)
    WorkflowRecords(admitted.store, admitted.get()["id"]).ingest_findings(reviewer["id"], [])
    assert admitted.status()["pending_review_attempts"] == []
