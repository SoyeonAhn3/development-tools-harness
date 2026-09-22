"""Explicit live P3-T4 scheduler check on a fresh disposable fixture copy.

Run with the harness Python and --live. The controller-authored fixture plan is
approved only inside this new test project; no Planner service call is claimed.
This checks T4 execution, not T5 recovery or T6/T7 final user acceptance.
"""

import argparse
import copy
import hashlib
import json
from pathlib import Path
import shutil
import uuid

from development_harness.codex_adapter import default_model
from development_harness.files import snapshot
from development_harness.isolated_validation import IsolatedValidator
from development_harness.model import HarnessError, digest
from development_harness.plan_schema import validate_plan
from development_harness.planning import Planning
from development_harness.project import load_project
from development_harness.store import default_home
from development_harness.worker_contract import save_record
from development_harness.workers import CodexWorker
from development_harness.workflow import Workflow


CHECK = {"argv": ["{python}", "-m", "pytest", "-q"], "kind": "pytest", "timeout": 45}
CONTROLLER_CHECKS = '''import subprocess,sys
import pytest
@pytest.mark.parametrize('args,stdout,success', [(['3'],'6\\n',True),(['0'],'0\\n',True),(['-1'],'',False),(['-42'],'',False),(['not-an-int'],'',False),([],'',False)])
def test_controller_requirement(args,stdout,success):
    result=subprocess.run([sys.executable,'cli.py',*args],capture_output=True,text=True,timeout=5)
    assert (result.returncode==0)==success
    assert result.stdout==stdout
    assert (result.stderr=='')==success
    if args and args[0] in ('-1','-42'):
        assert any(word in result.stderr.lower() for word in ('nonnegative','non-negative','negative','zero','>= 0'))
'''


def words(en, ko):
    return {"en": en, "ko": ko}


def fixture_plan():
    verification = words("Run the registered command-level pytest suite without skips or failures.",
                         "등록된 명령 수준 pytest 검사를 실패와 생략 없이 실행한다.")
    reuse = words("Preserve positive and zero doubling, missing-argument and non-integer rejection.",
                  "양수와 0의 두 배 출력 및 인수 누락·정수가 아닌 입력 거부를 유지한다.")
    reject = words("Reject negative integers with nonzero exit, empty stdout and clear nonnegative-input stderr.",
                   "음수는 0이 아닌 종료 코드와 빈 stdout, 음수 불가를 설명하는 stderr로 거부한다.")
    tests = words("Retain positive/zero command tests and add negative-input and invalid-argument regressions.",
                  "양수·0 명령 검사를 유지하고 음수 및 잘못된 인수 회귀 검사를 추가한다.")
    goal = words("Implement and independently review two ordered tasks in the disposable CLI fixture.",
                 "임시 CLI 예제에서 선행 관계가 있는 두 Task를 구현하고 독립 리뷰한다.")
    return {
        "overview": goal,
        "technology": words("Existing Python standard library and pytest only.", "기존 Python 표준 라이브러리와 pytest만 사용한다."),
        "current_phase": "P3-T4-SMOKE",
        "phases": [{"id": "P3-T4-SMOKE", "title": goal, "goal": goal, "exit_criteria": verification}],
        "tasks": [
            {"id": "T1", "title": reject, "requirements": ["R1", "R2", "R3"],
             "paths": ["cli.py", "test_cli.py"], "acceptance": reject,
             "verification": verification, "depends_on": []},
            {"id": "T2", "title": tests, "requirements": ["R1", "R2", "R3"],
             "paths": ["test_cli.py"],
             "acceptance": words("Keep T1 behavior and tests; strengthen boundary, missing-argument and non-integer command checks. If T1 already covers all cases, demonstrate that with the unchanged response.",
                                 "T1 동작과 검사를 보존하고 경계·인수 누락·정수가 아닌 입력의 명령 검사를 보완한다. T1이 이미 모두 다룬 경우 unchanged 응답으로 근거를 설명한다."),
             "verification": verification, "depends_on": ["T1"]},
        ],
        "requirements": [
            {"id": "R1", "text": reuse, "source_quote": "Preserve argparse handling of missing or non-integer arguments.",
             "disposition": "reuse", "phase_id": "P3-T4-SMOKE", "verification": verification, "rationale": reuse},
            {"id": "R2", "text": reject, "source_quote": "Reject negative integers with a nonzero exit code, no numeric stdout and\na clear stderr message explaining that the value must be nonnegative.",
             "disposition": "implement", "phase_id": "P3-T4-SMOKE", "verification": verification, "rationale": reject},
            {"id": "R3", "text": tests, "source_quote": "Use the existing Python standard library and pytest. Add command-level tests\nfor negative input and retain the positive and zero checks.",
             "disposition": "implement", "phase_id": "P3-T4-SMOKE", "verification": verification, "rationale": tests},
        ],
        "code_context": [
            {"path": "cli.py", "summary": words("Argparse integer doubling command; negative values initially accepted.", "정수를 두 배로 출력하며 초기에는 음수도 허용하는 argparse 명령이다."),
             "evidence": "print(args.value * 2)", "kind": "explicit"},
            {"path": "test_cli.py", "summary": words("Two real subprocess checks for zero and positive values.", "0과 양수를 실제 하위 프로세스로 확인하는 기본 검사 두 개다."),
             "evidence": '[(0, "0\\n"), (3, "6\\n")]', "kind": "explicit"},
        ],
        "questions": [],
    }


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--live", action="store_true", help="Allow real Developer/Reviewer calls in the disposable two-task fixture")
    parser.add_argument("--model")
    parser.add_argument("--codex-path")
    args = parser.parse_args()
    if not args.live:
        parser.error("Use --live to explicitly run the bounded fixture workflow with real AI calls.")
    model = args.model or default_model()
    directory = default_home().parent / "t4-live" / uuid.uuid4().hex[:12]
    directory.mkdir(parents=True)
    fixture = Path(__file__).resolve().parents[1] / "tests/fixtures/workflow_project"
    fixture_before = snapshot(fixture)
    project = directory / "project"
    shutil.copytree(fixture, project)
    report = {"scope": "P3-T4 disposable scheduler verification only", "directory": str(directory),
              "passed": False, "model": model, "planner_ai_calls": 0, "user_acceptance": False,
              "fixture_plan_source": "controller_fixture", "actual_ai_call_attempts": 0, "stages": {}}
    workflow = None

    def stage(name, value):
        report["stages"][name] = value
        save_record(directory / "report.json", report)
        print(json.dumps({"stage": name, "directory": str(directory)}, ensure_ascii=True), flush=True)

    class ObservedWorker(CodexWorker):
        def invoke(self, scope, **kwargs):
            stage("dispatch:" + kwargs["attempt"]["id"], {"role": self.role, "task_id": scope.task_id})
            result = super().invoke(scope, **kwargs)
            stage("response:" + result["attempt"]["id"], result)
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
            raise HarnessError("Fixture baseline did not pass without a Planner service call.")
        stage("baseline", planning["baseline_evidence"])
        plan = fixture_plan()
        _, files = load_project(project)
        validate_plan(plan, files, skill="writing_profile" in planning)
        planner._publish(planning, plan, source="controller_fixture")
        planner.approve()
        workflow = Workflow(project, planner.store.home)
        workflow.prepare()
        admitted = workflow.approve()
        approval = copy.deepcopy(admitted["approval"])
        starting = snapshot(project)
        stage("admission", {"planning_run_id": planning["id"], "workflow_run_id": admitted["id"],
                            "plan_hash": admitted["plan_hash"], "approval": approval,
                            "starting_content_version": digest(starting)})
        validator = ObservedValidator(directory / "validator")
        permissions = validator.verify()
        stage("permissions", {"ready": permissions["ready"], "directory": permissions["evidence_directory"]})
        completed = workflow.execute(worker_factory=ObservedWorker, validator_factory=lambda _: validator,
                                     codex_path=args.codex_path)
        stage("workflow", completed)
        status = workflow.status()
        stage("status", status)
        if completed["stage"] != "technically_complete":
            raise HarnessError("Workflow did not complete: " + str(completed.get("reason")))
        if completed["approval"] != approval or completed["content_version"] == digest(starting):
            raise HarnessError("Workflow approval changed or required implementation did not change the code.")
        if completed["content_version"] != digest(snapshot(project)):
            raise HarnessError("Final workflow evidence is not bound to the resulting project.")
        execution = completed["execution"]
        if execution["completed_tasks"] != ["T1", "T2"] or any(value > 2 for value in execution["corrections"].values()):
            raise HarnessError("The ordered Task completion or configured correction bound is invalid.")
        final_ids = set(execution["final_validation_ids"])
        final_checks = [item for item in completed["attempts"] if item["id"] in final_ids]
        if (len(final_checks) != len(completed["policy"]["validation"]) or
                any(item.get("outcome") != "passed" or item["content_version"] != completed["content_version"]
                    for item in final_checks)):
            raise HarnessError("Final Phase validation evidence is missing, failing or stale.")
        calls = [item for item in completed["attempts"] if item["role"] in {"developer", "reviewer"}]
        order = [item["task_id"] for item in calls]
        if set(order) != {"T1", "T2"} or order != sorted(order):
            raise HarnessError("Real role calls did not respect the admitted Task order.")
        sessions = [item.get("session_id") for item in calls]
        if any(not value for value in sessions) or len(set(sessions)) != len(sessions):
            raise HarnessError("Real roles did not each use a distinct confirmed session.")
        if any(item.get("outcome") != "validated" for item in calls):
            raise HarnessError("An unverified AI call remains in the completed workflow.")
        stage("role_order", [{key: item.get(key) for key in ("id", "task_id", "role", "session_id", "content_version")}
                             for item in calls])
        assertions = directory / "assertions"
        shutil.copytree(project, assertions)
        if snapshot(assertions) != snapshot(project):
            raise HarnessError("Independent verification copy differs from the final application.")
        (assertions / "test_controller_requirements.py").write_text(CONTROLLER_CHECKS, encoding="utf-8")
        independent = validator.run(dict(CHECK, argv=CHECK["argv"] + ["test_controller_requirements.py"]), assertions)
        independent["application_content_version"] = completed["content_version"]
        independent["controller_test_sha256"] = hashlib.sha256(CONTROLLER_CHECKS.encode()).hexdigest()
        stage("independent_requirements", independent)
        if independent["outcome"] != "passed" or independent["tests"] != 6:
            raise HarnessError("Independent command-level requirements did not all pass.")
        if digest(snapshot(project)) != completed["content_version"]:
            raise HarnessError("Independent checks changed the completed main project.")
        report["passed"] = True
    except Exception as exc:
        report["error"] = str(exc)
    finally:
        if workflow is not None:
            try:
                latest = workflow.get()
                report["actual_ai_call_attempts"] = sum(item.get("actual_ai_call_attempts", 0) for item in latest["attempts"])
                report["confirmed_ai_calls"] = sum(item.get("confirmed_ai_calls") or 0 for item in latest["attempts"])
                report["uncertain_ai_calls"] = sum(item.get("dispatch_status") == "uncertain" for item in latest["attempts"])
                report["workflow_stage"] = latest["stage"]
            except (HarnessError, OSError) as exc:
                report["status_error"] = str(exc)
                report["passed"] = False
        report["fixture_preserved"] = snapshot(fixture) == fixture_before
        report["passed"] = report["passed"] and report["fixture_preserved"]
        save_record(directory / "report.json", report)
    print(json.dumps({key: value for key, value in report.items() if key != "stages"}, ensure_ascii=True, indent=2), flush=True)
    return 0 if report["passed"] else 1


if __name__ == "__main__":
    raise SystemExit(main())
