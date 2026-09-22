import copy
import hashlib
import json
from pathlib import Path
import sys

import pytest

from development_harness.model import HarnessError, digest
from development_harness.processes import alive
from development_harness.worker_contract import TaskScope
from development_harness.workers import CodexWorker


@pytest.fixture
def transport(tmp_path):
    project = tmp_path / "project"
    project.mkdir()
    (project / "value.py").write_text("VALUE = 1\n")
    scope = TaskScope(project, "T1", {"R1": "Return one"}, ["value.py"], [])
    worker = CodexWorker("developer", "local-fixture", tmp_path / "worker")
    worker.exe = Path(sys.executable)
    worker.policy = {"binary_hash": hashlib.sha256(worker.exe.read_bytes()).hexdigest()}
    response = {"task_id": "T1", "status": "unchanged", "summary": "Already implemented",
                "changes": [], "questions": []}
    script = """
import json
from pathlib import Path
import sys

prompt = sys.stdin.read()
if prompt:
    Path('received.txt').write_text(prompt)
print(json.dumps({'type': 'thread.started', 'thread_id': 'local-session'}), flush=True)
print(json.dumps({'type': 'item.completed', 'item': {'type': 'agent_message', 'text': sys.argv[1]}}))
print(json.dumps({'type': 'turn.completed'}), flush=True)
"""
    worker.arguments = lambda _: [sys.executable, "-c", script, json.dumps(response)]
    attempt = {"id": "controller-attempt", "task_id": "T1", "role": "developer",
               "content_version": digest(scope.baseline), "input_hash": None,
               "plan_hash": "approved-plan", "policy_hash": "approved-policy", "outcome": "prepared"}
    return worker, scope, attempt


def test_controller_identity_and_observed_lifecycle_are_preserved(transport):
    worker, scope, attempt = transport
    phases = []

    def persist(record, phase):
        assert record is attempt
        assert record[phase + "_at"] > 0
        if phase in {"prepared", "process_registered", "dispatch_intent"}:
            assert not (worker.directory / "received.txt").exists()
        if phase == "process_registered":
            assert alive(record["process"])
            assert record["actual_ai_call_attempts"] == 0
            assert record["confirmed_ai_calls"] == 0
        if phase == "dispatch_intent":
            assert record["dispatch_status"] == "uncertain"
            assert record["confirmed_ai_calls"] is None
        phases.append((phase, copy.deepcopy(record)))

    result = worker.invoke(scope, attempt=attempt, lifecycle=persist)
    assert result["attempt"] is attempt
    assert [phase for phase, _ in phases] == ["prepared", "process_registered", "dispatch_intent", "responded", "finished"]
    assert attempt["id"] == "controller-attempt"
    assert attempt["input_hash"] == digest(scope.packet())
    assert attempt["plan_hash"] == "approved-plan"
    assert attempt["policy_hash"] == "approved-policy"
    assert attempt["session_id"] == "local-session"
    assert attempt["usage"] is None
    assert attempt["confirmed_ai_calls"] == 1
    assert attempt["outcome"] == "validated"
    assert not alive(attempt["process"])
    assert json.loads((worker.directory / "attempt.json").read_text())["finished_at"] == attempt["finished_at"]


@pytest.mark.parametrize("field,value", [("id", ""), ("task_id", "T2"), ("role", "reviewer"),
                                         ("content_version", "changed"), ("input_hash", "changed"),
                                         ("outcome", "interrupted"), ("dispatch_status", "uncertain")])
def test_attempt_identity_mismatch_prevents_external_process(transport, field, value):
    worker, scope, attempt = transport
    attempt[field] = value
    with pytest.raises(HarnessError, match="attempt does not match"):
        worker.invoke(scope, attempt=attempt)
    assert not (worker.directory / "events.jsonl").exists()


@pytest.mark.parametrize("failed_phase", ["prepared", "process_registered", "dispatch_intent"])
def test_persistence_failure_before_dispatch_prevents_prompt_and_preserves_original(transport, failed_phase):
    worker, scope, attempt = transport
    original = OSError("primary persistence failure")
    observed = []

    def persist(record, phase):
        observed.append(phase)
        if phase == failed_phase:
            raise original
        if phase == "finished":
            raise OSError("secondary final persistence failure")

    with pytest.raises(OSError, match="primary persistence failure") as caught:
        worker.invoke(scope, attempt=attempt, lifecycle=persist)
    assert caught.value is original
    assert "secondary final persistence failure" in " ".join(original.__notes__)
    assert not (worker.directory / "received.txt").exists()
    assert observed[-1] == "finished"
    if attempt.get("process"):
        assert not alive(attempt["process"])
    assert attempt["outcome"] == "unverified"


@pytest.mark.parametrize("interrupted", [False, True])
def test_failed_call_preserves_observed_session_and_unknown_usage(transport, interrupted):
    worker, scope, attempt = transport
    script = """
import json
import sys
import time
sys.stdin.read()
print(json.dumps({'type': 'thread.started', 'thread_id': 'failed-session'}), flush=True)
print('{partial', flush=True)
""" + ("time.sleep(60)" if interrupted else "sys.exit(4)")
    worker.arguments = lambda _: [sys.executable, "-c", script]
    phases = []
    with pytest.raises(HarnessError, match="timeout" if interrupted else "call failed"):
        worker.invoke(scope, attempt=attempt, lifecycle=lambda record, phase: phases.append(phase), timeout=1)
    assert attempt["session_id"] == "failed-session"
    assert attempt["usage"] is None
    assert attempt["confirmed_ai_calls"] is None
    assert attempt["dispatch_status"] == "uncertain"
    assert "responded" not in phases
    assert phases[-1] == "finished"
    assert not alive(attempt["process"])
    if interrupted:
        assert attempt["ended"] is attempt["duration"] is None


def test_failed_response_persistence_retains_confirmed_response(transport):
    worker, scope, attempt = transport

    def persist(record, phase):
        if phase == "responded":
            raise OSError("response persistence failed")

    with pytest.raises(OSError, match="response persistence failed"):
        worker.invoke(scope, attempt=attempt, lifecycle=persist)
    assert attempt["confirmed_ai_calls"] == 1
    assert attempt["session_id"] == "local-session"
    assert attempt["outcome"] == "unverified"
    assert not alive(attempt["process"])
