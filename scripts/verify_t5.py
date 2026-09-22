"""Explicit live T5 recovery check: one Developer, a real crash, one Reviewer.

All project edits and execution stay in a fresh disposable external fixture.
The controller-authored plan uses a real baseline but no Planner AI call.
"""

import argparse
import copy
import hashlib
import json
import os
from pathlib import Path
import shutil
import subprocess
import sys
import uuid

from development_harness.codex_adapter import default_model
from development_harness.files import snapshot
from development_harness.isolated_validation import IsolatedValidator
from development_harness.model import HarnessError, digest, file_digest
from development_harness.plan_schema import validate_plan
from development_harness.planning import Planning
from development_harness.processes import ensure_stopped
from development_harness.project import load_project
from development_harness.store import default_home
from development_harness.worker_contract import save_record
from development_harness.workers import CodexWorker
from development_harness.workflow import Workflow
from development_harness.workflow_records import WorkflowRecords, effective_attempt

from verify_t4 import CHECK, CONTROLLER_CHECKS, fixture_plan, words


def recovery_plan():
    plan = fixture_plan()
    phase = "P3-T5-SMOKE"
    goal = words("Recover one real Developer response after a controller crash and independently review its CLI changes.",
                 "실제 Developer 응답 저장 후 제어 프로그램을 종료하고 응답을 복구해 CLI 변경을 독립 리뷰한다.")
    plan.update(current_phase=phase, overview=goal)
    plan["phases"][0].update(id=phase, title=goal, goal=goal)
    for requirement in plan["requirements"]:
        requirement["phase_id"] = phase
    plan["tasks"] = plan["tasks"][:1]
    plan["tasks"][0]["acceptance"] = words(
        "Reject negative integers with nonzero exit, empty stdout and clear nonnegative-input stderr; preserve positive/zero doubling and missing/non-integer rejection. Add command-level negative regressions while retaining the existing positive/zero tests.",
        "음수를 0이 아닌 종료 코드·빈 stdout·음수 불가를 설명하는 stderr로 거부한다. 양수·0 출력과 누락·비정수 인수 거부를 유지하고 음수 명령 회귀 검사를 추가한다.")
    return plan


def crash_controller(directory, codex_path):
    """Die after the durable response, before the final lifecycle callback."""
    directory = Path(directory).resolve(strict=True)
    allowed = (default_home().parent / "t5-live").resolve()
    if not directory.is_relative_to(allowed) or directory == allowed:
        raise HarnessError("The crash controller requires a disposable t5-live directory.")
    from development_harness import workers
    original = workers.save_record

    def save_then_exit(path, value):
        original(path, value)
        if Path(path).name == "response.json":
            original(directory / "crash.json", {"boundary": "developer_response_saved",
                     "response": str(path), "response_sha256": file_digest(path), "exit_code": 99})
            os._exit(99)

    workers.save_record = save_then_exit
    workflow = Workflow(directory / "project", directory / "state")
    workflow.execute(codex_path=codex_path, steps=1)
    raise HarnessError("The Developer did not reach the intended saved-response crash boundary.")


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--live", action="store_true", help="Allow at most one real Developer and one real Reviewer call")
    parser.add_argument("--model")
    parser.add_argument("--codex-path")
    parser.add_argument("--controller", help=argparse.SUPPRESS)
    args = parser.parse_args()
    if not args.live:
        parser.error("Use --live to explicitly run the bounded recovery fixture with real AI calls.")
    if args.controller:
        return crash_controller(args.controller, args.codex_path)

    model = args.model or default_model()
    directory = default_home().parent / "t5-live" / uuid.uuid4().hex[:12]
    directory.mkdir(parents=True)
    fixture = Path(__file__).resolve().parents[1] / "tests/fixtures/workflow_project"
    fixture_before = snapshot(fixture)
    project = directory / "project"
    shutil.copytree(fixture, project)
    report = {"scope": "P3-T5 disposable response recovery verification only", "directory": str(directory),
              "passed": False, "model": model, "planner_ai_calls": 0, "user_acceptance": False,
              "fixture_plan_source": "controller_fixture", "max_corrections": 0, "live_call_limit": 2,
              "validator_storage": "cached short external path; default per-attempt storage tested separately",
              "actual_ai_call_attempts": 0, "stages": {}}
    workflow = None

    def stage(name, value):
        report["stages"][name] = value
        save_record(directory / "report.json", report)
        print(json.dumps({"stage": name, "directory": str(directory)}, ensure_ascii=True), flush=True)

    class ReviewerOnly(CodexWorker):
        calls = 0

        def invoke(self, scope, **kwargs):
            if self.role != "reviewer" or type(self).calls:
                raise HarnessError("Live recovery verification forbids additional Developer or Reviewer calls.")
            type(self).calls += 1
            stage("reviewer_dispatch", {"attempt_id": kwargs["attempt"]["id"], "task_id": scope.task_id})
            result = super().invoke(scope, **kwargs)
            stage("reviewer_response", result)
            return result

    class ObservedValidator(IsolatedValidator):
        def run(self, check, project, **kwargs):
            result = super().run(check, project, **kwargs)
            stage("validation:" + result["id"], result)
            return result

    try:
        planner = Planning(project, directory / "state")
        planner.register({"version": 1, "spec": "spec.md", "context": ["cli.py", "test_cli.py"],
                          "model": model, "planner_timeout": 240, "validation": [CHECK]})
        planning = planner.plan(baseline_only=True)
        if planning["stage"] != "planning" or any(item["role"] == "planner" for item in planning["attempts"]):
            raise HarnessError("The controller fixture baseline did not pass without a Planner service call.")
        stage("baseline", planning["baseline_evidence"])
        plan = recovery_plan()
        _, files = load_project(project)
        validate_plan(plan, files, skill="writing_profile" in planning)
        planner._publish(planning, plan, source="controller_fixture")
        planner.approve()
        workflow = Workflow(project, planner.store.home)
        workflow.prepare(max_corrections=0)
        admitted = workflow.approve()
        approval = copy.deepcopy(admitted["approval"])
        starting = snapshot(project)
        stage("admission", {"planning_run_id": planning["id"], "workflow_run_id": admitted["id"],
                            "plan_hash": admitted["plan_hash"], "approval": approval,
                            "starting_content_version": digest(starting)})
        validator = ObservedValidator(directory / "validator")
        permissions = validator.verify()
        stage("permissions", {"ready": permissions["ready"], "directory": permissions["evidence_directory"]})
        command = [sys.executable, str(Path(__file__).resolve()), "--live", "--controller", str(directory)]
        if args.codex_path:
            command.extend(["--codex-path", args.codex_path])
        stage("developer_controller_start", {"stdout": str(directory / "controller.stdout.log"),
                                             "stderr": str(directory / "controller.stderr.log")})
        with (directory / "controller.stdout.log").open("wb") as output, (directory / "controller.stderr.log").open("wb") as error:
            child = subprocess.run(command, stdout=output, stderr=error, timeout=360,
                                   creationflags=subprocess.CREATE_NO_WINDOW)
        if child.returncode != 99 or not (directory / "crash.json").exists():
            raise HarnessError("The real Developer controller did not stop at the intended durable-response boundary.")
        interrupted = workflow.get()
        calls_before = [item for item in interrupted["attempts"] if item["role"] in {"developer", "reviewer"}]
        if (len(calls_before) != 1 or calls_before[0]["role"] != "developer"
                or "finished" in calls_before[0]["journal_phases"]
                or not interrupted["execution"]["in_flight"] or snapshot(project) != starting):
            raise HarnessError("The crash did not leave exactly one unapplied, unfinished Developer response.")
        developer_before = copy.deepcopy(calls_before[0])
        ensure_stopped(interrupted["attempts"])
        events_before = workflow.store.events(interrupted["id"])
        assessment = workflow.recovery_status()
        if workflow.store.events(interrupted["id"]) != events_before or workflow.get() != interrupted:
            raise HarnessError("Recovery inspection changed the controller journal.")
        stage("interruption", {"exit_code": child.returncode, "workflow": interrupted,
                               "crash": json.loads((directory / "crash.json").read_text()),
                               "assessment": assessment, "processes_stopped": True})
        if not assessment["available"] or assessment["action"] != "reuse":
            raise HarnessError("The saved real response was not eligible for reuse: " + assessment["reason"])
        repaired = workflow.resume(worker_factory=ReviewerOnly, validator_factory=lambda _: validator,
                                   codex_path=args.codex_path, steps=1)
        if (len(repaired["attempts"]) != 1 or ReviewerOnly.calls != 0
                or repaired["execution"]["stage"] != "validation"
                or repaired["execution"]["corrections"] != {"T1": 0}):
            raise HarnessError("Response recovery repeated a call or changed the correction budget.")
        preserved = {key: value for key, value in repaired["attempts"][0].items() if key != "recovery"}
        if preserved != developer_before or repaired["approval"] != approval:
            raise HarnessError("Recovery replaced the original Developer observations or execution approval.")
        stage("response_reused", repaired)
        completed = workflow.resume(worker_factory=ReviewerOnly, validator_factory=lambda _: validator,
                                    codex_path=args.codex_path)
        stage("workflow", completed)
        stage("status", workflow.status())
        if completed["stage"] != "technically_complete":
            raise HarnessError("Recovered workflow did not complete: " + str(completed.get("reason")))
        execution = completed["execution"]
        if (completed["approval"] != approval or execution["completed_tasks"] != ["T1"]
                or execution["corrections"] != {"T1": 0}
                or completed["content_version"] == digest(starting)
                or completed["content_version"] != digest(snapshot(project))):
            raise HarnessError("The recovered final content, approval, task order or correction budget is invalid.")
        calls = [effective_attempt(item) for item in completed["attempts"] if item["role"] in {"developer", "reviewer"}]
        sessions = [item.get("session_id") for item in calls]
        if ([item["role"] for item in calls] != ["developer", "reviewer"] or ReviewerOnly.calls != 1
                or any(item.get("outcome") != "validated" or item.get("confirmed_ai_calls") != 1 for item in calls)
                or any(not item for item in sessions) or len(set(sessions)) != 2):
            raise HarnessError("Recovery did not retain exactly two independently confirmed real role sessions.")
        final_ids = set(execution["final_validation_ids"])
        final_checks = [item for item in completed["attempts"] if item["id"] in final_ids]
        if (len(final_checks) != len(completed["policy"]["validation"])
                or any(item.get("outcome") != "passed" or item["content_version"] != completed["content_version"]
                       for item in final_checks)):
            raise HarnessError("Final required validation is missing, failing or bound to different content.")
        events = workflow.store.events(completed["id"])
        if (workflow.resume(worker_factory=ReviewerOnly, validator_factory=lambda _: validator) != completed
                or workflow.store.events(completed["id"]) != events):
            raise HarnessError("Resuming the completed workflow duplicated work or journal records.")
        stage("role_sessions", [{key: item.get(key) for key in ("id", "role", "session_id", "content_version", "response_hash")}
                                 for item in calls])
        assertions = directory / "assertions"
        shutil.copytree(project, assertions)
        if snapshot(assertions) != snapshot(project):
            raise HarnessError("Independent requirement checks copied different application content.")
        (assertions / "test_controller_requirements.py").write_text(CONTROLLER_CHECKS, encoding="utf-8")
        independent = validator.run(dict(CHECK, argv=CHECK["argv"] + ["test_controller_requirements.py"]), assertions)
        independent["application_content_version"] = completed["content_version"]
        independent["controller_test_sha256"] = hashlib.sha256(CONTROLLER_CHECKS.encode()).hexdigest()
        stage("independent_requirements", independent)
        if independent["outcome"] != "passed" or independent["tests"] != 6:
            raise HarnessError("Independent positive/zero/negative/missing/invalid CLI checks did not all pass.")
        if digest(snapshot(project)) != completed["content_version"]:
            raise HarnessError("Independent checks changed the completed application.")
        report["passed"] = True
    except Exception as exc:
        report["error"] = str(exc)
    finally:
        if workflow is not None:
            try:
                latest = workflow.get()
                summary = WorkflowRecords(workflow.store, latest["id"]).summary()
                report.update(actual_ai_call_attempts=summary["ai_dispatch_attempts"],
                              confirmed_ai_calls=summary["confirmed_ai_calls"], uncertain_ai_calls=summary["uncertain_ai_calls"],
                              workflow_stage=latest["stage"], final_content_version=latest["content_version"],
                              workflow_run_id=latest["id"])
                save_record(directory / "final-run.json", latest)
            except (HarnessError, OSError) as exc:
                report.update(status_error=str(exc), passed=False)
        report["fixture_preserved"] = snapshot(fixture) == fixture_before
        report["passed"] = report["passed"] and report["fixture_preserved"]
        save_record(directory / "report.json", report)
    print(json.dumps({key: value for key, value in report.items() if key != "stages"}, ensure_ascii=True, indent=2), flush=True)
    return 0 if report["passed"] else 1


if __name__ == "__main__":
    raise SystemExit(main())
