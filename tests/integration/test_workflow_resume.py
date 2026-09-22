"""T5 recovery after actual controller-process death at durable boundaries.

AI responses use local subprocess fixtures; no external AI service is called.
Most tests isolate journal decisions with recorded validation. The validation
crash and final validation test execute the real Windows AppContainer backend.
"""

import copy
import os
from pathlib import Path
import subprocess
import sys
import time

import pytest

from development_harness.files import snapshot
from development_harness.model import HarnessError, digest
from development_harness.processes import Job, alive, identity
from development_harness.workflow import Workflow
from development_harness.workflow_records import WorkflowRecords, effective_attempt
from test_workflow import (FIRST, TESTS, admitted_factory, developer,
                           isolated_factory, reviewer, scripted_workers)


CRASH_EXIT = 73
ADDED_TESTS = TESTS + "\ndef test_new_requirement():\n    assert A == 1\n"


class PassingValidator:
    """A recorded outcome with a real contained child, for recovery decisions."""
    def __init__(self, directory):
        pass

    def verify(self):
        return {"ready": True, "test_fixture": True}

    def run(self, check, project, *, launched, attempt_id):
        started = time.time()
        job = Job()
        worker = subprocess.Popen([sys.executable, "-c", "import sys; sys.stdin.buffer.read()"],
                                  stdin=subprocess.PIPE, stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL,
                                  creationflags=subprocess.CREATE_NO_WINDOW)
        try:
            job.assign(worker.pid)
            evidence = {"id": attempt_id, "content_version": digest(snapshot(project)),
                        "check_hash": digest(check), "argv": check["argv"], "outcome": "running",
                        "started": started, "ended": None, "duration": None, "tests": 0,
                        "process": identity(worker.pid), "containment": job.record, "test_fixture": True}
            launched(evidence)
            worker.communicate(b"fixture", timeout=15)
            assert worker.returncode == 0
        finally:
            job.close()
            worker.wait(timeout=10)
            if worker.stdin and not worker.stdin.closed:
                worker.stdin.close()
        ended = time.time()
        return evidence | {"outcome": "passed", "ended": ended, "duration": ended - started,
                           "tests": 1, "exit_code": 0}


def _controller_crash(project, home, mode):
    """Executed in a disposable child; patches stop the controller, never production hooks."""
    import development_harness.worker_contract as contract_module
    import development_harness.workers as workers_module
    from development_harness.isolated_validation import IsolatedValidator
    from development_harness.store import Store

    workflow = Workflow(project, home)
    script = [developer(text=FIRST), reviewer()]
    validator_factory = PassingValidator
    if mode in {"before_dispatch", "dispatch_uncertain"}:
        original = WorkflowRecords.lifecycle
        target_phase = "process_registered" if mode == "before_dispatch" else "dispatch_intent"

        def stop_lifecycle(self, attempt, phase):
            result = original(self, attempt, phase)
            if attempt["role"] == "developer" and phase == target_phase:
                os._exit(CRASH_EXIT)
            return result

        WorkflowRecords.lifecycle = stop_lifecycle
    elif mode == "response_saved":
        original = workers_module.save_record

        def stop_after_response(path, value):
            original(path, value)
            if Path(path).name == "response.json":
                os._exit(CRASH_EXIT)

        workers_module.save_record = stop_after_response
    elif mode == "partial_patch":
        script = [developer(files={"value.py": FIRST, "test_value.py": ADDED_TESTS}), reviewer()]
        original = contract_module.apply_write

        def stop_after_first_write(root, name, content, expected):
            original(root, name, content, expected)
            os._exit(CRASH_EXIT)

        contract_module.apply_write = stop_after_first_write
    elif mode == "files_applied":
        original = Store.transition

        def stop_before_patch_commit(self, run_id, event_id, kind, detail, update):
            if kind == "execution_boundary" and detail.get("next_stage") == "validation":
                os._exit(CRASH_EXIT)
            return original(self, run_id, event_id, kind, detail, update)

        Store.transition = stop_before_patch_commit
    elif mode in {"review_before_ingestion", "review_after_ingestion"}:
        script = [developer(), reviewer(finding=True)]
        original = WorkflowRecords.ingest_findings

        def stop_at_ingestion(self, *args, **kwargs):
            if mode == "review_before_ingestion":
                os._exit(CRASH_EXIT)
            original(self, *args, **kwargs)
            os._exit(CRASH_EXIT)

        WorkflowRecords.ingest_findings = stop_at_ingestion
    elif mode == "validation_running":
        class CrashValidator(IsolatedValidator):
            def run(self, check, project, *, launched, attempt_id):
                def stop_launched(evidence):
                    launched(evidence)
                    os._exit(CRASH_EXIT)

                return super().run(check, project, launched=stop_launched, attempt_id=attempt_id)

        validator_factory = CrashValidator
    elif mode == "recovery_write":
        import development_harness.workflow_recovery as recovery_module
        original = recovery_module.apply_write

        def stop_recovery_write(*args, **kwargs):
            original(*args, **kwargs)
            os._exit(CRASH_EXIT)

        recovery_module.apply_write = stop_recovery_write
        workflow.resume(worker_factory=scripted_workers([reviewer()]), validator_factory=PassingValidator)
        raise AssertionError("Expected interruption while repairing the missing file")
    elif mode == "recovery_patch_intent":
        original = Store.transition

        def stop_after_patch_intent(self, run_id, event_id, kind, detail, update):
            result = original(self, run_id, event_id, kind, detail, update)
            if kind == "patch_application_started":
                os._exit(CRASH_EXIT)
            return result

        Store.transition = stop_after_patch_intent
        workflow.resume(worker_factory=scripted_workers([reviewer()]), validator_factory=PassingValidator)
        raise AssertionError("Expected interruption after durable patch intent")
    else:
        raise AssertionError("Unknown controller interruption fixture: " + mode)
    result = workflow.execute(worker_factory=scripted_workers(script), validator_factory=validator_factory)
    raise AssertionError("Expected the controller to terminate; result was " + repr(result.get("reason")))


def crash(workflow, mode):
    code = "import sys; sys.path.insert(0, sys.argv[1]); from test_workflow_resume import _controller_crash; _controller_crash(*sys.argv[2:])"
    result = subprocess.run([sys.executable, "-c", code, str(Path(__file__).parent),
                             str(workflow.project), str(workflow.store.home), mode],
                            capture_output=True, text=True, timeout=120,
                            creationflags=subprocess.CREATE_NO_WINDOW)
    assert result.returncode == CRASH_EXIT, result.stdout + result.stderr
    run = workflow.get()
    assert run["execution"]["in_flight"] is True
    deadline = time.monotonic() + 5
    while any(alive(attempt.get("process")) for attempt in run["attempts"]) and time.monotonic() < deadline:
        time.sleep(0.05)
    assert all(not alive(attempt.get("process")) for attempt in run["attempts"])
    return run


def assessment(workflow, action):
    before = workflow.get()
    events = workflow.store.events(before["id"])
    files = snapshot(workflow.project)
    result = workflow.recovery_status()
    assert result["action"] == action, result
    assert result["available"] == (action not in {"blocked", "terminal"})
    assert workflow.get() == before
    assert workflow.store.events(before["id"]) == events
    assert snapshot(workflow.project) == files
    return result


def finish(workflow, worker, validator=PassingValidator):
    result = workflow.resume(worker_factory=worker, validator_factory=validator)
    assert result["stage"] == "technically_complete", result.get("reason")
    assert not worker.pending, list(worker.pending)
    assert result["execution"]["corrections"] == {"T1": 0}
    assert result["execution"]["completed_tasks"] == ["T1"]
    assert "inspection_error" not in workflow.status()
    return result


def test_unsent_process_is_retired_and_retry_does_not_count_as_an_extra_ai_call(admitted_factory):
    workflow = admitted_factory(tasks=1)
    interrupted = crash(workflow, "before_dispatch")
    attempt = interrupted["attempts"][0]
    assert attempt["dispatch_status"] == "not_sent"
    assert attempt["actual_ai_call_attempts"] == 0
    assessment(workflow, "retry")
    worker = scripted_workers([developer(text=FIRST), reviewer()])
    result = finish(workflow, worker)
    assert result["attempts"][0]["id"] == attempt["id"]
    assert result["attempts"][0]["actual_ai_call_attempts"] == 0
    summary = WorkflowRecords(workflow.store, result["id"]).summary()
    assert summary["ai_dispatch_attempts"] == summary["confirmed_ai_calls"] == 2
    assert len([a for a in result["attempts"] if a["role"] == "developer"]) == 2


def test_uncertain_dispatch_never_retries_or_invents_completion(admitted_factory):
    workflow = admitted_factory(tasks=1)
    interrupted = crash(workflow, "dispatch_uncertain")
    assert interrupted["attempts"][0]["dispatch_status"] == "uncertain"
    assessment(workflow, "blocked")
    worker = scripted_workers([])
    with pytest.raises(HarnessError):
        workflow.resume(worker_factory=worker, validator_factory=PassingValidator)
    assert workflow.get() == interrupted
    summary = WorkflowRecords(workflow.store, interrupted["id"]).summary()
    assert summary["ai_dispatch_attempts"] == summary["uncertain_ai_calls"] == 1
    assert summary["total_ai_calls"] is None
    assert not worker.calls


@pytest.mark.parametrize("mode,action", [("response_saved", "reuse"), ("files_applied", "repair")])
def test_saved_developer_result_is_reused_without_a_second_developer_call(admitted_factory, mode, action):
    workflow = admitted_factory(tasks=1)
    interrupted = crash(workflow, mode)
    original_id = interrupted["attempts"][0]["id"]
    initial_approval = copy.deepcopy(interrupted["approval"])
    assessment(workflow, action)
    worker = scripted_workers([reviewer()])
    result = finish(workflow, worker)
    developers = [attempt for attempt in result["attempts"] if attempt["role"] == "developer"]
    assert len(developers) == 1 and developers[0]["id"] == original_id
    assert effective_attempt(developers[0])["outcome"] == "validated"
    assert result["approval"] == initial_approval
    assert len(result["execution"]["patches"]) == 1
    assert (workflow.project / "value.py").read_text(encoding="utf-8") == FIRST
    assert WorkflowRecords(workflow.store, result["id"]).summary()["confirmed_ai_calls"] == 2


def test_partial_patch_repairs_only_missing_file_without_rewriting_applied_file(admitted_factory):
    workflow = admitted_factory(tasks=1)
    interrupted = crash(workflow, "partial_patch")
    changed = workflow.project / "value.py"
    unchanged = workflow.project / "test_value.py"
    assert changed.read_text(encoding="utf-8") == FIRST
    assert unchanged.read_text(encoding="utf-8") == TESTS
    applied_mtime = changed.stat().st_mtime_ns
    assessment(workflow, "repair")
    worker = scripted_workers([reviewer()])
    result = finish(workflow, worker)
    assert changed.stat().st_mtime_ns == applied_mtime
    assert unchanged.read_text(encoding="utf-8") == ADDED_TESTS
    assert result["attempts"][0]["id"] == interrupted["attempts"][0]["id"]
    assert len([a for a in result["attempts"] if a["role"] == "developer"]) == 1


def test_second_controller_crash_during_repair_can_resume_without_reapplying_files(admitted_factory):
    workflow = admitted_factory(tasks=1)
    interrupted = crash(workflow, "partial_patch")
    crash(workflow, "recovery_write")
    changed = workflow.project / "value.py"
    tests = workflow.project / "test_value.py"
    assert changed.read_text(encoding="utf-8") == FIRST
    assert tests.read_text(encoding="utf-8") == ADDED_TESTS
    mtimes = changed.stat().st_mtime_ns, tests.stat().st_mtime_ns
    assessment(workflow, "repair")
    result = finish(workflow, scripted_workers([reviewer()]))
    assert (changed.stat().st_mtime_ns, tests.stat().st_mtime_ns) == mtimes
    assert result["attempts"][0]["id"] == interrupted["attempts"][0]["id"]
    assert len([a for a in result["attempts"] if a["role"] == "developer"]) == 1


def test_recovery_can_change_from_response_reuse_to_patch_repair_after_another_crash(admitted_factory):
    workflow = admitted_factory(tasks=1)
    interrupted = crash(workflow, "response_saved")
    assessment(workflow, "reuse")
    second = crash(workflow, "recovery_patch_intent")
    pending = second["execution"]["patch_pending"]
    assert pending["attempt_id"] == interrupted["attempts"][0]["id"]
    assert not (Path(pending["directory"]) / "patch.json").exists()
    assert snapshot(workflow.project) == interrupted["expected"]
    assessment(workflow, "repair")
    result = finish(workflow, scripted_workers([reviewer()]))
    assert len(result["execution"]["patches"]) == 1
    assert len([a for a in result["attempts"] if a["role"] == "developer"]) == 1
    assert (workflow.project / "value.py").read_text(encoding="utf-8") == FIRST
    assert WorkflowRecords(workflow.store, result["id"]).summary()["ai_dispatch_attempts"] == 2


@pytest.mark.parametrize("edited", ["value.py", "test_value.py"])
def test_partial_patch_preserves_user_edits_and_blocks_all_recovery_writes(admitted_factory, edited):
    workflow = admitted_factory(tasks=1)
    crash(workflow, "partial_patch")
    (workflow.project / edited).write_text("# User edit after the crash.\n", encoding="utf-8", newline="\n")
    before = snapshot(workflow.project)
    saved = workflow.get()
    assessment(workflow, "blocked")
    worker = scripted_workers([])
    with pytest.raises(HarnessError):
        workflow.resume(worker_factory=worker, validator_factory=PassingValidator)
    assert workflow.get() == saved
    assert snapshot(workflow.project) == before
    assert not worker.calls


@pytest.mark.parametrize("mode", ["review_before_ingestion", "review_after_ingestion"])
def test_saved_review_ingestion_is_idempotent_and_mandatory_finding_is_not_lost(admitted_factory, mode):
    workflow = admitted_factory(tasks=1)
    interrupted = crash(workflow, mode)
    old_review = next(a for a in interrupted["attempts"] if a["role"] == "reviewer")
    assert old_review["outcome"] == "validated"
    assessment(workflow, "reuse")
    worker = scripted_workers([developer(text=FIRST), reviewer(resolve=True)])
    result = workflow.resume(worker_factory=worker, validator_factory=PassingValidator)
    assert result["stage"] == "technically_complete", result.get("reason")
    assert not worker.pending
    assert result["execution"]["corrections"] == {"T1": 1}
    assert len(result["findings"]) == 1
    finding = next(iter(result["findings"].values()))
    observations = [item for item in finding["history"] if item["kind"] == "observed"]
    assert len(observations) == 1 and observations[0]["attempt_id"] == old_review["id"]
    assert finding["status"] == "resolved"
    assert WorkflowRecords(workflow.store, result["id"]).summary()["confirmed_ai_calls"] == 4
    events = workflow.store.events(result["id"])
    assert workflow.resume(worker_factory=worker, validator_factory=PassingValidator) == result
    assert workflow.store.events(result["id"]) == events


def test_running_real_isolated_validation_is_retried_then_final_content_is_revalidated(admitted_factory, isolated_factory):
    workflow = admitted_factory(tasks=1)
    interrupted = crash(workflow, "validation_running")
    validation = next(a for a in interrupted["attempts"] if a["role"] == "validation")
    assert validation["outcome"] == "running" and validation["backend"] == "appcontainer"
    assert validation["ended"] is validation["duration"] is None
    assessment(workflow, "retry")
    worker = scripted_workers([reviewer()])
    result = finish(workflow, worker, isolated_factory)
    checks = [a for a in result["attempts"] if a["role"] == "validation"]
    assert len(checks) == 3
    assert checks[0]["id"] == validation["id"]
    assert checks[0]["ended"] is checks[0]["duration"] is None
    assert all(a["outcome"] == "passed" and a["backend"] == "appcontainer" for a in checks[1:])
    assert checks[-1]["id"] in result["execution"]["final_validation_ids"]
    assert checks[-1]["content_version"] == digest(snapshot(workflow.project))
    assert len([a for a in result["attempts"] if a["role"] == "developer"]) == 1


@pytest.mark.parametrize("metadata", ["directory", "file"])
def test_git_metadata_changes_do_not_invalidate_saved_response_recovery(admitted_factory, metadata):
    workflow = admitted_factory(tasks=1)
    crash(workflow, "response_saved")
    git = workflow.project / ".git"
    if metadata == "directory":
        git.mkdir()
        (git / "HEAD").write_text("ref: refs/heads/user-branch\n", encoding="utf-8")
    else:
        git.write_text("gitdir: ../user-worktree-metadata\n", encoding="utf-8")
    assessment(workflow, "reuse")
    result = finish(workflow, scripted_workers([reviewer()]))
    assert result["stage"] == "technically_complete"
    assert git.exists()


@pytest.mark.parametrize("terminal", ["cancelled", "failed"])
def test_cancelled_or_failed_run_cannot_be_resurrected(admitted_factory, terminal):
    workflow = admitted_factory(tasks=1, max_corrections=0)
    if terminal == "cancelled":
        workflow.cancel()
    else:
        class FailingValidator(PassingValidator):
            def run(self, *args, **kwargs):
                return super().run(*args, **kwargs) | {"outcome": "failed", "failure_kind": "code", "exit_code": 1}

        workflow.execute(worker_factory=scripted_workers([developer(text=FIRST)]), validator_factory=FailingValidator)
    before = workflow.get()
    assert before["stage"] == terminal
    assessment(workflow, "terminal")
    worker = scripted_workers([])
    events = workflow.store.events(before["id"])
    assert workflow.resume(worker_factory=worker, validator_factory=PassingValidator) == before
    assert workflow.store.events(before["id"]) == events
    assert not worker.calls
