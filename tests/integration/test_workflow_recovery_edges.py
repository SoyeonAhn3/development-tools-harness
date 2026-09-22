"""Recovery preserves completed failure decisions and the real CLI boundary."""

import json
from pathlib import Path
import subprocess
import sys
import time

import pytest

from development_harness.files import snapshot
from development_harness.model import HarnessError, digest
from development_harness.processes import Job, alive, identity
from development_harness.workflow_records import WorkflowRecords
from test_workflow import FIRST, admitted_factory, developer, reviewer, scripted_workers
from test_workflow_resume import PassingValidator, crash


def cli(workflow, *arguments, expected=0):
    result = subprocess.run([sys.executable, "-m", "development_harness", "--project", str(workflow.project),
                             "--state-dir", str(workflow.store.home), *arguments], capture_output=True,
                            text=True, timeout=30, creationflags=subprocess.CREATE_NO_WINDOW)
    assert result.returncode == expected, result.stdout + result.stderr
    return json.loads(result.stdout or result.stderr)


@pytest.mark.parametrize("mode", ["response_saved", "partial_patch"])
def test_cli_resume_reuses_result_without_launching_the_selected_missing_codex(admitted_factory, mode):
    workflow = admitted_factory(tasks=1)
    before = crash(workflow, mode)
    status = cli(workflow, "workflow-status", expected=int(mode == "partial_patch"))
    assert status["recovery"]["available"]
    result = cli(workflow, "workflow-resume", "--steps", "1", "--codex-path", str(workflow.store.home / "missing.exe"))
    assert result["stage"] == "executing" and result["execution"]["stage"] == "validation"
    assert len(result["attempts"]) == 1
    assert result["confirmed_ai_calls"] == result["ai_dispatch_attempts"] == 1
    assert result["approval"] == before["approval"]
    assert result["recoveries"][0]["status"] == "completed"


def test_cli_uncertain_resume_returns_error_and_preserves_all_records(admitted_factory):
    workflow = admitted_factory(tasks=1)
    before = crash(workflow, "dispatch_uncertain")
    events = workflow.store.events(before["id"])
    result = cli(workflow, "workflow-resume", expected=2)
    assert "artifact" in result["error"].lower()
    assert workflow.get() == before
    assert workflow.store.events(before["id"]) == events


@pytest.mark.parametrize("limit", [0, 2])
def test_interrupted_failure_decision_does_not_bypass_or_duplicate_correction_budget(admitted_factory, monkeypatch, limit):
    workflow = admitted_factory(tasks=1, max_corrections=limit)

    class Failed(PassingValidator):
        def run(self, *args, **kwargs):
            return super().run(*args, **kwargs) | {"outcome": "failed", "failure_kind": "code", "exit_code": 1}

    original = workflow.store.transition
    def interrupt(run_id, event_id, kind, detail, update):
        if kind == "validation_result_recorded":
            raise KeyboardInterrupt()
        return original(run_id, event_id, kind, detail, update)
    monkeypatch.setattr(workflow.store, "transition", interrupt)
    workflow.execute(worker_factory=scripted_workers([developer()]), validator_factory=Failed)
    monkeypatch.setattr(workflow.store, "transition", original)
    failed = workflow.get()["attempts"][-1]
    assert failed["outcome"] == "failed"
    worker = scripted_workers([developer(text=FIRST)])
    recovered = workflow.resume(worker_factory=worker, validator_factory=PassingValidator, steps=1)
    assert recovered["execution"]["corrections"]["T1"] == int(limit > 0)
    assert recovered["attempts"][-1] == failed
    if limit:
        assert recovered["execution"]["stage"] == "developer"
        continued = workflow.resume(worker_factory=worker, validator_factory=PassingValidator, steps=1)
        assert continued["execution"]["corrections"]["T1"] == 1
        assert len(worker.calls) == 1
    else:
        assert recovered["stage"] == "failed"
        assert workflow.resume(worker_factory=worker, validator_factory=PassingValidator) == recovered
        assert not worker.calls


@pytest.mark.parametrize("outcome,kind,exit_code", [("no_tests", "validation_incomplete", 5),
                                                    ("unverified", "environment", 2)])
def test_completed_incomplete_check_is_not_relabelled_as_interrupted(admitted_factory, monkeypatch, outcome, kind, exit_code):
    workflow = admitted_factory(tasks=1)
    class Incomplete(PassingValidator):
        def run(self, *args, **kwargs):
            return super().run(*args, **kwargs) | {"outcome": outcome, "failure_kind": kind, "exit_code": exit_code}
    original = workflow.store.transition
    def interrupt(run_id, event_id, event, detail, update):
        if event == "validation_result_recorded":
            raise KeyboardInterrupt()
        return original(run_id, event_id, event, detail, update)
    monkeypatch.setattr(workflow.store, "transition", interrupt)
    workflow.execute(worker_factory=scripted_workers([developer()]), validator_factory=Incomplete)
    monkeypatch.setattr(workflow.store, "transition", original)
    attempts = workflow.get()["attempts"]
    worker = scripted_workers([])
    result = workflow.resume(worker_factory=worker, validator_factory=PassingValidator)
    assert result["stage"] == "stopped" and result["execution"]["stop_kind"] == kind
    assert result["attempts"] == attempts
    assert result["execution"]["corrections"] == {"T1": 0}
    assert not worker.calls


def test_editor_process_racing_repair_cannot_be_overwritten(admitted_factory, monkeypatch):
    import development_harness.workflow_recovery as recovery
    workflow = admitted_factory(tasks=1)
    crash(workflow, "partial_patch")
    original = recovery.apply_write
    user_text = "# Saved concurrently by the user.\n"
    def edited(root, name, content, expected):
        result = subprocess.run([sys.executable, "-c", "from pathlib import Path; import sys; Path(sys.argv[1]).write_text(sys.argv[2],encoding='utf-8',newline='\\n')",
                                 str(root / name), user_text], capture_output=True, timeout=15,
                                creationflags=subprocess.CREATE_NO_WINDOW)
        assert result.returncode == 0, result.stderr
        return original(root, name, content, expected)
    monkeypatch.setattr(recovery, "apply_write", edited)
    with pytest.raises(HarnessError, match="File changed"):
        workflow.resume(worker_factory=scripted_workers([]), validator_factory=PassingValidator)
    assert (workflow.project / "test_value.py").read_text(encoding="utf-8") == user_text
    before = snapshot(workflow.project)
    assert workflow.recovery_status()["action"] == "blocked"
    assert snapshot(workflow.project) == before


def test_final_validation_timeout_can_resume_without_reauthorizing_or_repeating_ai(admitted_factory):
    workflow = admitted_factory(tasks=1)
    approval = workflow.get()["approval"]

    class FinalTimeout(PassingValidator):
        """Use an actual contained deadline to produce the final interrupted result."""
        def __init__(self, directory):
            self.count = 0

        def run(self, check, project, *, launched, attempt_id):
            self.count += 1
            if self.count == 1:
                return super().run(check, project, launched=launched, attempt_id=attempt_id)
            job = Job()
            process = subprocess.Popen(
                [sys.executable, "-c", "import sys,time; sys.stdin.buffer.read(); time.sleep(60)"],
                stdin=subprocess.PIPE, stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL,
                creationflags=subprocess.CREATE_NO_WINDOW)
            try:
                job.assign(process.pid)
                evidence = {"id": attempt_id, "content_version": digest(snapshot(project)),
                            "check_hash": digest(check), "argv": check["argv"], "outcome": "running",
                            "started": time.time(), "ended": None, "duration": None, "tests": 0,
                            "process": identity(process.pid), "containment": job.record, "test_fixture": True}
                launched(evidence)
                with pytest.raises(subprocess.TimeoutExpired):
                    process.communicate(b"fixture", timeout=0.1)
            finally:
                job.close()
                process.wait(timeout=10)
                if process.stdin and not process.stdin.closed:
                    process.stdin.close()
            return evidence | {"outcome": "interrupted", "failure_kind": "interrupted",
                               "exit_code": process.returncode, "reason": "Validation deadline; process tree terminated."}

    worker = scripted_workers([developer(text=FIRST), reviewer()])
    stopped = workflow.execute(worker_factory=worker, validator_factory=FinalTimeout)
    assert stopped["stage"] == "stopped" and stopped["execution"]["stop_kind"] == "final_interrupted"
    original = stopped["attempts"][-1]
    assert original["outcome"] == "interrupted" and not alive(original["process"])
    assert original["ended"] is original["duration"] is None
    assert stopped["execution"]["completed_tasks"] == ["T1"]
    before = WorkflowRecords(workflow.store, stopped["id"]).summary()
    files = snapshot(workflow.project)
    assert workflow.recovery_status()["action"] == "retry"
    resumed_worker = scripted_workers([])
    result = workflow.resume(worker_factory=resumed_worker, validator_factory=PassingValidator)
    assert result["stage"] == "technically_complete", result.get("reason")
    assert result["approval"] == approval
    assert result["execution"]["corrections"] == {"T1": 0}
    assert snapshot(workflow.project) == files
    assert not resumed_worker.calls
    after = WorkflowRecords(workflow.store, result["id"]).summary()
    for key in ("ai_dispatch_attempts", "confirmed_ai_calls", "total_ai_calls"):
        assert after[key] == before[key]
    assert [wait for wait in result["waits"] if wait["reason"] == "execution_approval"] == stopped["waits"]
    acceptance_waits = [wait for wait in result["waits"] if wait["reason"] == "result_acceptance"]
    assert len(acceptance_waits) == 1 and acceptance_waits[0]["ended"] is None
    assert after["observed_approval_wait"] == before["observed_approval_wait"]
    assert after["approval_wait"] is None
    validations = [attempt for attempt in result["attempts"] if attempt["role"] == "validation"]
    assert len(validations) == 3
    assert validations[-2]["id"] == original["id"]
    assert validations[-2]["ended"] is validations[-2]["duration"] is None
    assert validations[-1]["outcome"] == "passed"
    assert result["execution"]["final_validation_ids"] == [validations[-1]["id"]]
