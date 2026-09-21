import json

import pytest

from development_harness.model import HarnessError, digest
from development_harness.worker_contract import TaskScope
from development_harness.workers import CodexWorker


@pytest.fixture
def calls(tmp_path, monkeypatch):
    project = tmp_path / "project"
    project.mkdir()
    (project / "value.py").write_text("VALUE = 1\n")
    scope = TaskScope(project, "T1", {"R1": "Return one"}, ["value.py"], [])
    seen = []
    def verify(adapter):
        adapter.policy = {"ready": True, "boundary": "unit test transport"}
        return adapter.policy
    def generate(adapter, prompt, schema, attempt, launched, timeout):
        seen.append((adapter.role, prompt))
        attempt.update(outcome="running", log=str(adapter.directory / "events.jsonl"))
        launched(attempt)
        (adapter.directory / "events.jsonl").write_text(json.dumps({"type": "thread.started", "thread_id": adapter.directory.name}) + "\n")
        if adapter.role == "developer":
            return {"task_id": "T1", "status": "unchanged", "summary": "Already implemented", "changes": [], "questions": []}
        return {"task_id": "T1", "verdict": "pass", "summary": "Requirement verified", "findings": [], "questions": []}
    monkeypatch.setattr(CodexWorker, "verify", verify)
    monkeypatch.setattr(CodexWorker, "generate", generate)
    return scope, seen


def test_real_role_contracts_use_separate_single_use_sessions(calls, tmp_path):
    scope, seen = calls
    developer = CodexWorker("developer", "test-model", tmp_path / "developer")
    dev = developer.invoke(scope)
    reviewer = CodexWorker("reviewer", "test-model", tmp_path / "reviewer")
    review = reviewer.invoke(scope, before=scope.files, validation=[{"content_version": digest(scope.baseline), "outcome": "passed"}])
    assert dev["attempt"]["session_id"] != review["attempt"]["session_id"]
    assert dev["attempt"]["actual_ai_call_attempts"] == review["attempt"]["actual_ai_call_attempts"] == 1
    assert [entry[0] for entry in seen] == ["developer", "reviewer"]
    assert "independent read-only Reviewer" in seen[1][1]
    with pytest.raises(HarnessError, match="fresh session"):
        developer.invoke(scope)


def test_stale_validation_is_rejected_before_ai_call(calls, tmp_path):
    scope, seen = calls
    worker = CodexWorker("reviewer", "test-model", tmp_path / "reviewer")
    with pytest.raises(HarnessError, match="current code version"):
        worker.invoke(scope, before=scope.files, validation=[{"content_version": "stale", "outcome": "passed"}])
    assert seen == []


@pytest.mark.parametrize("outcome", ["failed", "no_tests", "unverified", "interrupted"])
def test_ai_pass_cannot_override_failed_validation(calls, tmp_path, outcome):
    scope, seen = calls
    worker = CodexWorker("reviewer", "test-model", tmp_path / "reviewer")
    with pytest.raises(HarnessError, match="cannot pass"):
        worker.invoke(scope, before=scope.files, validation=[{"content_version": digest(scope.baseline), "outcome": outcome}])
    attempt = json.loads((worker.directory / "attempt.json").read_text())
    assert attempt["outcome"] == "unverified"
    assert not (worker.directory / "response.json").exists()


def test_project_edit_during_role_call_invalidates_result(calls, tmp_path, monkeypatch):
    scope, _ = calls
    original = CodexWorker.generate
    def changed(*args):
        result = original(*args)
        (scope.project / "value.py").write_text("user change\n")
        return result
    monkeypatch.setattr(CodexWorker, "generate", changed)
    worker = CodexWorker("developer", "test-model", tmp_path / "developer")
    with pytest.raises(HarnessError, match="Unexpected file changes"):
        worker.invoke(scope)
    assert (scope.project / "value.py").read_text() == "user change\n"


def test_controller_artifacts_cannot_be_placed_in_project(calls):
    scope, seen = calls
    worker = CodexWorker("developer", "test-model", scope.project / "unsafe-artifacts")
    with pytest.raises(HarnessError, match="outside the project"):
        worker.invoke(scope)
    assert seen == []
