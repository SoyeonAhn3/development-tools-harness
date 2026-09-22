"""T4 scheduler with real worker subprocess journals and isolated pytest results.

The worker responses are deterministic local fixtures, not AI-service evidence.
Validation executes the real project under the verified Windows AppContainer.
"""

from collections import deque
import copy
import json
from pathlib import Path
import sys
import time
import uuid

import pytest

from development_harness.files import snapshot
from development_harness.isolated_validation import IsolatedValidator
from development_harness.model import HarnessError, digest, file_digest
from development_harness.planning import Planning
from development_harness.processes import ProjectLock
from development_harness.store import default_home
from development_harness.workers import CodexWorker
from development_harness.workflow import Workflow


INITIAL = "A = 0\nB = 0\n"
FIRST = "A = 1\nB = 0\n"
FINAL = "A = 1\nB = 2\n"
TESTS = "from value import A, B\ndef test_values():\n    assert A in {0, 1}\n    assert B in {0, 2}\n"
CHECK = {"argv": ["{python}", "-m", "pytest", "-q"], "kind": "pytest", "timeout": 15}


@pytest.fixture(scope="module")
def isolated_factory():
    directory = default_home().parent / "t4-tests" / uuid.uuid4().hex[:12]
    validator = IsolatedValidator(directory / "validator")
    report = validator.verify()
    assert report["ready"] and report["checks"]["standard_user"], report

    class VerifiedValidator:
        """Reuse permission proof; real run still rechecks runtime hashes every time."""
        def __init__(self, unused_directory):
            pass

        def verify(self):
            return report

        def run(self, *args, **kwargs):
            return validator.run(*args, **kwargs)

    return VerifiedValidator


@pytest.fixture
def admitted_factory(tmp_path):
    def create(*, tasks=2, max_corrections=2, checks=None):
        project = tmp_path / ("Workflow project 한글 " + uuid.uuid4().hex[:6])
        project.mkdir()
        (project / "spec.md").write_text("Set A to 1. Then set B to 2 while preserving A.\n", encoding="utf-8", newline="\n")
        (project / "value.py").write_text(INITIAL, encoding="utf-8", newline="\n")
        (project / "test_value.py").write_text(TESTS, encoding="utf-8", newline="\n")
        words = {"en": "Implement sequential values", "ko": "값을 순서대로 구현한다"}
        plan = {
            "overview": words, "technology": {"en": "Python and pytest", "ko": "Python과 pytest"},
            "current_phase": "P1",
            "phases": [{"id": "P1", "title": words, "goal": words, "exit_criteria": words}],
            "tasks": [{"id": "T" + str(index), "title": words, "requirements": ["R1"],
                       "paths": ["value.py", "test_value.py"], "acceptance": words,
                       "verification": words, "depends_on": [] if index == 1 else ["T1"]}
                      for index in range(1, tasks + 1)],
            "requirements": [{"id": "R1", "text": words, "source_quote": "Set A to 1.",
                              "disposition": "implement", "phase_id": "P1", "verification": words,
                              "rationale": words}],
            "code_context": [{"path": "value.py", "summary": words, "evidence": "A = 0", "kind": "explicit"}],
            "questions": [],
        }

        class FixturePlanner:
            def __init__(self, model, directory):
                Path(directory).mkdir(parents=True, exist_ok=True)

            def verify(self):
                return {"boundary": "local planning fixture, no AI service"}

            def generate(self, prompt, schema, attempt, launched, timeout):
                attempt.update(outcome="running")
                launched(attempt)
                attempt.update(ended=time.time(), duration=0.0, outcome="responded")
                return copy.deepcopy(plan)

        state_home = default_home().parent / "t4-tests" / uuid.uuid4().hex[:12] / "state"
        planner = Planning(project, state_home)
        planner.register({"version": 1, "spec": "spec.md", "context": ["value.py"],
                          "model": "local-test-model", "planner_timeout": 30,
                          "validation": checks or [CHECK]})
        planned = planner.plan(adapter_factory=FixturePlanner)
        assert planned["stage"] == "awaiting_plan_approval", planned.get("reason")
        planner.approve()
        workflow = Workflow(project, planner.store.home)
        workflow.prepare(max_corrections=max_corrections)
        workflow.approve()
        return workflow

    return create


def developer(task="T1", text=None, **extra):
    return {"role": "developer", "task": task, "files": {} if text is None else {"value.py": text}, **extra}


def reviewer(task="T1", **extra):
    return {"role": "reviewer", "task": task, **extra}


def scripted_workers(steps):
    pending, calls = deque(copy.deepcopy(steps)), []

    class LocalWorker(CodexWorker):
        def verify(self):
            self.exe = Path(sys.executable)
            self.policy = {"binary_hash": file_digest(self.exe), "profile": "text-only-v1", "test_transport": True}
            return self.policy

        def invoke(self, scope, **kwargs):
            assert pending, "Scheduler made an unexpected additional worker call"
            instruction = pending.popleft()
            assert (self.role, scope.task_id) == (instruction["role"], instruction["task"])
            self.instruction = instruction
            self.response = {"task_id": scope.task_id, "summary": "Deterministic local worker response", "questions": []}
            if self.role == "developer":
                changes = [{"path": name, "base_sha256": scope.baseline.get(name, "absent"), "content": text}
                           for name, text in instruction.get("files", {}).items()]
                self.response.update(status="changes" if changes else "unchanged", changes=changes)
                if instruction.get("blocked"):
                    self.response.update(status="blocked", changes=[], questions=["Clarify the missing requirement."])
            else:
                self.response.update(verdict="pass", findings=[])
                if instruction.get("finding"):
                    self.response.update(verdict="changes", findings=[{
                        "id": "value-invalid", "requirement_id": "R1", "path": "value.py",
                        "severity": "high", "required": True, "evidence": "A still does not implement R1.",
                        "recommendation": "Set A to the required value and retain existing tests.",
                    }])
                if instruction.get("blocked"):
                    self.response.update(verdict="blocked", findings=[], questions=["Clarify the required behavior."])
            if instruction.get("assert_locked"):
                with pytest.raises(HarnessError, match="owns this project"):
                    with ProjectLock(instruction["assert_locked"]):
                        pytest.fail("Scheduler released the project lock while a worker was active")
            result = super().invoke(scope, **kwargs)
            packet = json.loads((self.directory / "input.json").read_text(encoding="utf-8"))
            calls.append({"role": self.role, "task": scope.task_id, "packet": packet,
                          "attempt": copy.deepcopy(result["attempt"])})
            return result

        def arguments(self, schema=None):
            packet = json.loads((self.directory / "input.json").read_text(encoding="utf-8"))
            prior = packet.get("prior_findings", [])
            if self.role == "reviewer" and prior:
                status = "resolved" if self.instruction.get("resolve") else "open"
                self.response["assessments"] = [{"finding_id": item["id"], "status": status,
                    "reason": "Confirmed against the current source and registered tests.",
                    "evidence": "The implementation and new passing validation establish this assessment."} for item in prior]
                if status == "open":
                    self.response["verdict"] = "changes"
                    self.response["findings"] = [{"id": item["id"], "requirement_id": item["requirement_id"],
                        "path": item["path"], "severity": item["severity"], "required": item["required"],
                        "evidence": "The previously reported defect is still present.",
                        "recommendation": "Implement the requirement before completing the task."} for item in prior]
            events = [{"type": "thread.started", "thread_id": "local-" + self.directory.name},
                      {"type": "turn.started"},
                      {"type": "item.completed", "item": {"type": "agent_message", "text": json.dumps(self.response)}},
                      {"type": "turn.completed"}]
            output = "\n".join(json.dumps(event) for event in events)
            code = "import sys; sys.stdin.buffer.read(); print(" + repr(output) + ")"
            return [sys.executable, "-c", code]

    LocalWorker.calls = calls
    LocalWorker.pending = pending
    return LocalWorker


def execute(workflow, worker, validator):
    result = workflow.execute(worker_factory=worker, validator_factory=validator)
    assert not worker.pending, {"remaining": list(worker.pending), "reason": result.get("reason")}
    assert result == workflow.get()
    return result


def test_ordered_tasks_preserve_approval_and_validate_final_content(admitted_factory, isolated_factory):
    workflow = admitted_factory()
    initial = workflow.get()
    worker = scripted_workers([developer(text=FIRST), reviewer(), developer("T2", FINAL), reviewer("T2")])
    result = execute(workflow, worker, isolated_factory)
    assert result["stage"] == "technically_complete", result.get("reason")
    assert result["execution"]["completed_tasks"] == ["T1", "T2"]
    assert result["execution"]["corrections"] == {"T1": 0, "T2": 0}
    assert result["approval"] == initial["approval"]
    assert result["baseline"] == initial["baseline"]
    assert result["content_version"] == digest(snapshot(workflow.project)) != initial["content_version"]
    assert (workflow.project / "value.py").read_text(encoding="utf-8") == FINAL
    assert "inspection_error" not in workflow.status()
    attempts = result["attempts"]
    assert [(a["task_id"], a["role"]) for a in attempts[:6]] == [
        ("T1", "developer"), ("T1", "validation"), ("T1", "reviewer"),
        ("T2", "developer"), ("T2", "validation"), ("T2", "reviewer")]
    final_ids = result["execution"]["final_validation_ids"]
    final_checks = [a for a in attempts if a["id"] in final_ids]
    assert len(final_checks) == 1
    assert final_checks[0]["outcome"] == "passed"
    assert final_checks[0]["content_version"] == result["content_version"]
    assert final_checks[0]["backend"] == "appcontainer"
    assert final_checks[0]["id"] != attempts[4]["id"]
    assert len({call["attempt"]["session_id"] for call in worker.calls}) == 4
    for call, expected in [(worker.calls[1], INITIAL), (worker.calls[3], FIRST)]:
        before = {item["path"]: item["text"] for item in call["packet"]["before"]}
        assert before["value.py"] == expected
        assert all(v["content_version"] == call["packet"]["content_version"] for v in call["packet"]["validation"])


@pytest.mark.parametrize("corrections", [0, 2])
def test_real_test_failure_exhausts_exact_shared_correction_budget(admitted_factory, isolated_factory, corrections):
    workflow = admitted_factory(max_corrections=corrections)
    worker = scripted_workers([developer(text="A = -1\nB = 0\n")] * (corrections + 1))
    result = execute(workflow, worker, isolated_factory)
    assert result["stage"] == "failed", result.get("reason")
    assert result["execution"]["corrections"]["T1"] == corrections
    assert result["execution"]["completed_tasks"] == []
    assert len([a for a in result["attempts"] if a["role"] == "developer"]) == corrections + 1
    checks = [a for a in result["attempts"] if a["role"] == "validation"]
    assert len(checks) == corrections + 1 and all(a["outcome"] == "failed" for a in checks)
    assert not any(a["task_id"] == "T2" or a["role"] == "reviewer" for a in result["attempts"])
    assert workflow.execute(worker_factory=worker, validator_factory=isolated_factory) == result


def test_real_failure_is_fixed_and_reviewer_keeps_original_before_image(admitted_factory, isolated_factory):
    workflow = admitted_factory(tasks=1)
    worker = scripted_workers([developer(text="A = -1\nB = 0\n"), developer(text=FIRST), reviewer()])
    result = execute(workflow, worker, isolated_factory)
    assert result["stage"] == "technically_complete", result.get("reason")
    assert result["execution"]["corrections"]["T1"] == 1
    assert worker.calls[1]["packet"]["feedback"]
    before = {item["path"]: item["text"] for item in worker.calls[-1]["packet"]["before"]}
    assert before["value.py"] == INITIAL
    assert [a["outcome"] for a in result["attempts"] if a["role"] == "validation"] == ["failed", "passed", "passed"]


@pytest.mark.parametrize("source,timeout,outcome", [
    ("def test_pass():\n    pass\nimport pytest\n@pytest.mark.skip(reason='required case')\ndef test_skip():\n    pass\n", 15, "unverified"),
    ("def helper_only():\n    pass\n", 15, "no_tests"),
    ("import required_dependency_not_installed\n", 15, "unverified"),
    ("def test_dependency():\n    import required_dependency_not_installed\n", 15, "failed"),
    ("def test_permission():\n    raise PermissionError('required resource denied')\n", 15, "failed"),
    ("import time\ndef test_wait():\n    time.sleep(60)\n", 2, "interrupted"),
])
def test_incomplete_real_validation_stops_without_advancing_or_consuming_budget(
        admitted_factory, isolated_factory, source, timeout, outcome):
    workflow = admitted_factory(checks=[dict(CHECK, timeout=timeout)])
    worker = scripted_workers([developer(files={"test_value.py": source})])
    result = execute(workflow, worker, isolated_factory)
    assert result["stage"] == "stopped", result.get("reason")
    assert result["execution"]["completed_tasks"] == []
    assert result["execution"]["corrections"]["T1"] == 0
    attempts = result["attempts"]
    assert [a["role"] for a in attempts] == ["developer", "validation"]
    assert attempts[-1]["outcome"] == outcome
    assert attempts[-1]["backend"] == "appcontainer"
    if outcome == "interrupted":
        assert attempts[-1]["ended"] is attempts[-1]["duration"] is None


def test_repeated_mandatory_finding_keeps_identity_and_blocks_next_task(admitted_factory, isolated_factory):
    workflow = admitted_factory(max_corrections=2)
    worker = scripted_workers([developer(), reviewer(finding=True), developer(), reviewer(finding=True),
                               developer(), reviewer(finding=True)])
    result = execute(workflow, worker, isolated_factory)
    assert result["stage"] == "failed", result.get("reason")
    assert result["execution"]["corrections"]["T1"] == 2
    assert result["execution"]["completed_tasks"] == []
    assert len(result["findings"]) == 1
    finding = next(iter(result["findings"].values()))
    assert finding["required"] is True and finding["status"] == "open"
    assert len([event for event in finding["history"] if event["kind"] == "observed"]) == 3
    assert all(a["task_id"] == "T1" for a in result["attempts"])


def test_test_failure_and_review_correction_share_one_budget(admitted_factory, isolated_factory):
    workflow = admitted_factory(tasks=1)
    worker = scripted_workers([developer(text="A = -1\nB = 0\n"), developer(text=INITIAL),
                               reviewer(finding=True), developer(text=FIRST), reviewer(resolve=True)])
    result = execute(workflow, worker, isolated_factory)
    assert result["stage"] == "technically_complete", result.get("reason")
    assert result["execution"]["corrections"]["T1"] == 2
    finding = next(iter(result["findings"].values()))
    assert finding["status"] == "resolved"
    assert workflow.status()["blocking_findings"] == []
    reviews = [call for call in worker.calls if call["role"] == "reviewer"]
    assert all(next(f["text"] for f in c["packet"]["before"] if f["path"] == "value.py") == INITIAL for c in reviews)
    assert reviews[-1]["packet"]["prior_findings"][0]["id"] == finding["id"]


@pytest.mark.parametrize("role", ["developer", "reviewer"])
def test_blocked_role_stops_without_correction_or_next_task(admitted_factory, isolated_factory, role):
    workflow = admitted_factory()
    script = [developer(blocked=True)] if role == "developer" else [developer(text=FIRST), reviewer(blocked=True)]
    worker = scripted_workers(script)
    result = execute(workflow, worker, isolated_factory)
    assert result["stage"] == "stopped", result.get("reason")
    assert result["execution"]["corrections"]["T1"] == 0
    assert result["execution"]["completed_tasks"] == []
    assert all(a["task_id"] == "T1" for a in result["attempts"])


def test_actual_scheduler_holds_project_lock_across_worker_call(admitted_factory, isolated_factory):
    workflow = admitted_factory(tasks=1)
    worker = scripted_workers([developer(text=FIRST), reviewer()])
    worker.pending[0]["assert_locked"] = workflow.store
    result = execute(workflow, worker, isolated_factory)
    assert result["stage"] == "technically_complete", result.get("reason")


def test_permission_verification_error_is_recorded_and_stops_without_retry(admitted_factory):
    workflow = admitted_factory()
    worker = scripted_workers([developer(text=FIRST)])

    class DeniedValidator:
        def __init__(self, directory):
            pass

        def verify(self):
            raise HarnessError("Isolated validation permission verification failed in test")

    result = execute(workflow, worker, DeniedValidator)
    assert result["stage"] == "stopped", result.get("reason")
    assert result["execution"]["corrections"]["T1"] == 0
    assert result["execution"]["completed_tasks"] == []
    assert [a["role"] for a in result["attempts"]] == ["developer", "validation"]
    assert result["attempts"][-1]["outcome"] == "unverified"


def test_every_registered_check_runs_again_against_final_content(admitted_factory, isolated_factory):
    checks = [CHECK, dict(CHECK, argv=["{python}", "-m", "pytest", "-q", "test_value.py"])]
    workflow = admitted_factory(tasks=1, checks=checks)
    worker = scripted_workers([developer(text=FIRST), reviewer()])
    result = execute(workflow, worker, isolated_factory)
    assert result["stage"] == "technically_complete", result.get("reason")
    validation = [a for a in result["attempts"] if a["role"] == "validation"]
    assert len(validation) == 4
    final_ids = set(result["execution"]["final_validation_ids"])
    assert len(final_ids) == 2 and final_ids == {a["id"] for a in validation[-2:]}
    assert {a["check_hash"] for a in validation[-2:]} == {digest(check) for check in checks}
    assert all(a["content_version"] == result["content_version"] and a["outcome"] == "passed" for a in validation)
    assert {v["id"] for v in worker.calls[-1]["packet"]["validation"]} == {a["id"] for a in validation[:2]}


def test_final_validation_failure_prevents_technical_completion(admitted_factory):
    """Inject only an outcome sequence to isolate the final completion decision."""
    workflow = admitted_factory(tasks=1)
    worker = scripted_workers([developer(text=FIRST), reviewer()])
    outcomes = deque(["passed", "failed"])

    class OutcomeValidator:
        def __init__(self, directory):
            pass

        def verify(self):
            return {"ready": True, "test_fixture": True}

        def run(self, check, project, *, launched, attempt_id):
            evidence = {"id": attempt_id, "content_version": digest(snapshot(project)),
                        "check_hash": digest(check), "argv": check["argv"], "started": 100.0,
                        "ended": None, "duration": None, "outcome": "running", "tests": 0}
            launched(evidence)
            outcome = outcomes.popleft()
            return evidence | {"outcome": outcome, "tests": 1, "ended": 101.0, "duration": 1.0,
                               "exit_code": 0 if outcome == "passed" else 1,
                               "failure_kind": None if outcome == "passed" else "code"}

    result = execute(workflow, worker, OutcomeValidator)
    assert not outcomes
    assert result["stage"] == "failed", result.get("reason")
    assert result["execution"]["completed_tasks"] == ["T1"]
    assert result["execution"]["corrections"]["T1"] == 0
    assert result["attempts"][-1]["outcome"] == "failed"
    assert result["attempts"][-1]["id"] in result["execution"]["final_validation_ids"]


def test_invalid_worker_proposal_stops_before_applying_any_file(admitted_factory):
    workflow = admitted_factory()
    baseline = snapshot(workflow.project)
    worker = scripted_workers([developer(files={"outside_scope.py": "unauthorized = True\n"})])
    result = execute(workflow, worker, lambda _: pytest.fail("Invalid proposals cannot reach validation"))
    assert result["stage"] == "stopped", result.get("reason")
    assert result["execution"]["corrections"]["T1"] == 0
    assert result["execution"]["completed_tasks"] == []
    assert snapshot(workflow.project) == baseline
    assert result["attempts"][0]["outcome"] == "unverified"
