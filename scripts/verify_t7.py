"""Run the approved T7 external example; leave result acceptance to the user.

Use the prepared harness Python and --live. The bounded controller-authored
plan follows the reviewed CLI specification; no Planner AI call is claimed.
The script never records user reuse/manual attestations or accepts a result.
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
import time
import traceback
import uuid
import xml.etree.ElementTree as ET

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
from development_harness.workflow import Workflow
from development_harness.workflow_acceptance import final_validation, seal_validation
from development_harness.workflow_records import WorkflowRecords, effective_attempt

from verify_t4 import CHECK, words
from verify_t5 import recovery_plan


CONTROLLER_CHECKS = '''import json, subprocess, sys
import pytest

@pytest.mark.parametrize('args,stdout,success', [(['3'],'6\\n',True),(['0'],'0\\n',True),(['-1'],'',False),(['-42'],'',False),(['not-an-int'],'',False),([],'',False)])
def test_controller_requirement(args, stdout, success, record_property):
    result = subprocess.run([sys.executable, 'cli.py', *args], capture_output=True, text=True, timeout=5)
    record_property('cli_observation', json.dumps({'argv': ['python', 'cli.py', *args], 'exit_code': result.returncode, 'stdout': result.stdout, 'stderr': result.stderr}))
    assert (result.returncode == 0) == success
    assert result.stdout == stdout
    assert (result.stderr == '') == success
    if args and args[0] in ('-1', '-42'):
        assert any(word in result.stderr.lower() for word in ('nonnegative', 'non-negative', 'negative', 'zero', '>= 0'))
'''

MANUAL_CHECKS = [{
    "id": "M1", "requirement_ids": ["R2"],
    "procedure": "Inspect the actual isolated CLI observations for -1 and -42 in report.json and their linked JUnit evidence; confirm the message clearly explains that negative input is forbidden.",
    "expected": "Both inputs exit nonzero, produce no stdout, and explain the nonnegative input requirement on stderr.",
}]


def example_plan():
    plan = recovery_plan()
    phase = "P3-T7-EXAMPLE"
    goal = words(
        "Complete the reviewed negative-input CLI change with real independent roles, one interruption and recovery, final checks, and pending genuine user acceptance.",
        "검토된 CLI 음수 거부 변경을 실제 독립 역할, 중단 1회와 복구, 최종 검사까지 실행하고 실제 사용자 인수를 기다린다.")
    plan.update(current_phase=phase, overview=goal)
    plan["phases"][0].update(id=phase, title=goal, goal=goal)
    for requirement in plan["requirements"]:
        requirement["phase_id"] = phase
    return plan


def require_directory(directory):
    directory = Path(directory).resolve(strict=True)
    allowed = (default_home().parent / "t7-live").resolve()
    if directory == allowed or not directory.is_relative_to(allowed):
        raise HarnessError("T7 requires its disposable external t7-live directory.")
    return directory


def crash_controller(directory, codex_path):
    """Stop after the durable response, before its final lifecycle callback."""
    directory = require_directory(directory)
    from development_harness import workers
    original = workers.save_record

    def save_then_exit(path, value):
        original(path, value)
        if Path(path).name == "response.json":
            original(directory / "crash.json", {
                "boundary": "developer_response_saved_before_finished_journal",
                "response": str(path), "response_sha256": file_digest(path), "exit_code": 99,
            })
            os._exit(99)

    workers.save_record = save_then_exit
    workflow = Workflow(directory / "project", directory / "state")
    workflow.execute(codex_path=codex_path, steps=1)
    raise HarnessError("Developer did not reach the intended saved-response crash boundary.")


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--live", action="store_true", help="Run real Developer/Reviewer calls with at most two corrections")
    parser.add_argument("--model")
    parser.add_argument("--codex-path")
    parser.add_argument("--controller", help=argparse.SUPPRESS)
    args = parser.parse_args()
    if not args.live:
        parser.error("Use --live to run the explicitly approved bounded T7 example.")
    if args.controller:
        return crash_controller(args.controller, args.codex_path)

    model = args.model or default_model()
    directory = default_home().parent / "t7-live" / uuid.uuid4().hex[:12]
    directory.mkdir(parents=True)
    fixture = Path(__file__).resolve().parents[1] / "tests/fixtures/workflow_project"
    fixture_before = snapshot(fixture)
    project, state = directory / "project", directory / "state"
    shutil.copytree(fixture, project)
    report = {
        "scope": "P3-T7 external CLI example, pending genuine user attestations and acceptance",
        "directory": str(directory), "project": str(project), "state": str(state),
        "model": model, "planner_ai_calls": 0, "plan_source": "controller_fixture",
        "plan_basis": "Previously reviewed single-task negative-input specification and user instruction: T7 테스트 시작",
        "authorization": "User authorized this previously described bounded example, plan/execution approval and one intentional interruption; result acceptance is separate.",
        "max_corrections": 2, "technical_verification_passed": False,
        "t7_complete": False, "user_acceptance": False,
        "validator_storage": "Public CLI default per-attempt AppContainer storage",
        "script": str(Path(__file__).resolve()), "script_sha256": file_digest(Path(__file__)),
        "harness_source": snapshot(Path(__file__).resolve().parents[1] / "src"),
        "python": sys.executable, "fixture_hashes": fixture_before,
        "commands": [], "stages": {},
    }
    workflow = None

    def stage(name, value):
        report["stages"][name] = value
        save_record(directory / "report.json", report)
        print(json.dumps({"stage": name, "directory": str(directory)}, ensure_ascii=True), flush=True)

    def command(name, argv, *, timeout, expected=0):
        out, err = directory / (name + ".stdout.log"), directory / (name + ".stderr.log")
        record = {"name": name, "argv": argv, "cwd": str(Path.cwd()), "started": time.time(),
                  "stdout": str(out), "stderr": str(err), "timeout": timeout}
        report["commands"].append(record)
        stage(name + "_start", {"argv": argv})
        try:
            with out.open("wb") as output, err.open("wb") as error:
                child = subprocess.run(argv, stdout=output, stderr=error, timeout=timeout,
                                       creationflags=subprocess.CREATE_NO_WINDOW)
            record["exit_code"] = child.returncode
        finally:
            record.update(ended=time.time(), stdout_sha256=file_digest(out), stderr_sha256=file_digest(err))
            stage(name + "_end", record)
        if child.returncode != expected:
            raise HarnessError(name + " failed with exit " + str(child.returncode) + "; inspect " + str(err))

    cli = [sys.executable, "-m", "development_harness", "--project", str(project), "--state-dir", str(state)]
    resume = cli + ["workflow-resume"]
    if args.codex_path:
        resume += ["--codex-path", args.codex_path]

    try:
        planner = Planning(project, state)
        planner.register({"version": 1, "spec": "spec.md", "context": ["cli.py", "test_cli.py"],
                          "model": model, "planner_timeout": 240, "validation": [CHECK]})
        planning = planner.plan(baseline_only=True)
        if planning["stage"] != "planning" or any(a["role"] == "planner" for a in planning["attempts"]):
            raise HarnessError("The real original fixture baseline did not pass without a Planner call.")
        stage("baseline", planning["baseline_evidence"])
        plan = example_plan()
        _, files = load_project(project)
        validate_plan(plan, files, skill="writing_profile" in planning)
        save_record(directory / "reviewed-plan.json", plan)
        save_record(directory / "manual-check-definitions.json", MANUAL_CHECKS)
        planner._publish(planning, plan, source="controller_fixture")
        planner.approve()
        workflow = Workflow(project, state)
        prepared = workflow.prepare(max_corrections=2, manual_checks=MANUAL_CHECKS)
        if prepared["policy"].get("result_version") != 1:
            raise HarnessError("T7 requires the current sealed result/acceptance policy.")
        admitted = workflow.approve()
        approval, starting = copy.deepcopy(admitted["approval"]), snapshot(project)
        stage("admission", {"planning_run_id": planning["id"], "workflow_run_id": admitted["id"],
                            "plan_hash": admitted["plan_hash"], "policy_hash": admitted["policy_hash"],
                            "policy": admitted["policy"], "approval": approval,
                            "starting_content_version": digest(starting)})
        controller = [sys.executable, str(Path(__file__).resolve()), "--live", "--controller", str(directory)]
        if args.codex_path:
            controller += ["--codex-path", args.codex_path]
        command("developer_controller", controller, timeout=600, expected=99)
        interrupted = workflow.get()
        if (len(interrupted["attempts"]) != 1 or interrupted["attempts"][0]["role"] != "developer"
                or "finished" in interrupted["attempts"][0]["journal_phases"]
                or not interrupted["execution"]["in_flight"] or snapshot(project) != starting):
            raise HarnessError("Crash did not leave one unapplied, unfinished Developer response.")
        developer_before = copy.deepcopy(interrupted["attempts"][0])
        ensure_stopped(interrupted["attempts"])
        events_before = workflow.store.events(interrupted["id"])
        assessment = workflow.recovery_status()
        if workflow.store.events(interrupted["id"]) != events_before or workflow.get() != interrupted:
            raise HarnessError("Recovery inspection changed the journal.")
        stage("interruption", {"workflow": interrupted, "assessment": assessment,
                               "crash": json.loads((directory / "crash.json").read_text(encoding="utf-8")),
                               "processes_stopped": True})
        if not assessment["available"] or assessment["action"] != "reuse":
            raise HarnessError("Real saved response is not reusable: " + assessment["reason"])
        command("response_reuse_cli", resume + ["--steps", "1"], timeout=120)
        recovered = workflow.get()
        if (len(recovered["attempts"]) != 1 or recovered["execution"]["stage"] != "validation"
                or recovered["execution"]["corrections"] != {"T1": 0}
                or recovered["approval"] != approval):
            raise HarnessError("Recovery repeated a role call or changed the approved correction budget.")
        preserved = {key: value for key, value in recovered["attempts"][0].items() if key != "recovery"}
        if preserved != developer_before:
            raise HarnessError("Recovery replaced the original Developer observations.")
        stage("response_reused", {"developer_attempt_id": developer_before["id"],
                                  "additional_ai_calls": 0, "recovery": recovered["attempts"][0].get("recovery")})
        command("complete_cli", resume, timeout=2400)
        completed = workflow.get()
        execution = completed["execution"]
        if (completed["stage"] != "technically_complete" or completed["approval"] != approval
                or execution["completed_tasks"] != ["T1"]
                or not 0 <= execution["corrections"]["T1"] <= 2
                or completed["content_version"] == digest(starting)
                or completed["content_version"] != digest(snapshot(project))):
            raise HarnessError("Recovered workflow did not complete against its approved final content.")
        calls = [effective_attempt(a) for a in completed["attempts"] if a["role"] in {"developer", "reviewer"}]
        sessions = [a.get("session_id") for a in calls]
        if (calls[0]["id"] != developer_before["id"] or calls[-1]["role"] != "reviewer"
                or any(a.get("outcome") != "validated" or a.get("confirmed_ai_calls") != 1 for a in calls)
                or any(not value for value in sessions) or len(set(sessions)) != len(sessions)
                or sum(a["role"] == "developer" for a in calls) != 1 + execution["corrections"]["T1"]):
            raise HarnessError("Real role sessions or response reuse/correction accounting is invalid.")
        stage("role_sessions", [{key: a.get(key) for key in (
            "id", "role", "task_id", "session_id", "content_version", "response_hash")} for a in calls])
        stage("final_sealed_validation", final_validation(completed))
        events = workflow.store.events(completed["id"])
        command("completed_resume_cli", resume, timeout=120)
        if workflow.get() != completed or workflow.store.events(completed["id"]) != events:
            raise HarnessError("Resuming completed execution changed records or duplicated work.")

        assertions = directory / "assertions"
        shutil.copytree(project, assertions)
        if snapshot(assertions) != snapshot(project):
            raise HarnessError("Independent assertion copy differs from the final project.")
        (assertions / "test_controller_requirements.py").write_text(CONTROLLER_CHECKS, encoding="utf-8")
        validator = IsolatedValidator(directory / "controller-validation")
        permission = validator.verify()
        stage("independent_permissions", {"ready": permission["ready"], "directory": permission["evidence_directory"]})
        independent = validator.run(dict(CHECK, argv=CHECK["argv"] + ["test_controller_requirements.py"]), assertions)
        stage("independent_requirements", {**independent, "artifact_hashes": seal_validation(independent),
              "application_content_version": completed["content_version"],
              "controller_test_sha256": hashlib.sha256(CONTROLLER_CHECKS.encode()).hexdigest()})
        if independent["outcome"] != "passed" or independent["tests"] != 6:
            raise HarnessError("Independent CLI requirement checks did not all pass.")
        observations = [json.loads(p.attrib["value"]) for p in ET.parse(independent["junit"]).getroot().iter("property")
                        if p.attrib.get("name") == "cli_observation"]
        if len(observations) != 6 or digest(snapshot(project)) != completed["content_version"]:
            raise HarnessError("Actual CLI output evidence is incomplete or the final project changed.")
        stage("actual_cli_observations", observations)
        command("workflow_report_cli", cli + ["workflow-report"], timeout=120)
        result = workflow.report()
        save_record(directory / "workflow-result.json", result)
        if (not result["technical_complete"] or result["acceptance"]["ready"]
                or result["acceptance"].get("accepted") or completed.get("acceptance")
                or completed.get("reuse_evidence") or completed.get("manual_checks")
                or {r["requirement_id"] for r in result["reuse_evidence"] if r["status"] == "missing"} != {"R1"}
                or {m["id"] for m in result["manual_checks"] if m["status"] == "missing"} != {"M1"}):
            raise HarnessError("Expected genuine user reuse/manual confirmations and acceptance are not pending.")
        report.update(technical_verification_passed=True, final_content_version=completed["content_version"],
                      final_file_hashes=snapshot(project), pending_user_actions=result["acceptance"]["blockers"],
                      final_validation_ids=execution["final_validation_ids"],
                      result_report=str(directory / "workflow-result.json"),
                      inspection_argv=cli + ["workflow-report"])
        stage("ready_for_user_review", {"technical_complete": True, "acceptance": result["acceptance"]})
    except BaseException as exc:
        report.update(error=str(exc), error_type=type(exc).__name__, traceback=traceback.format_exc())
        raise
    finally:
        if workflow is not None:
            try:
                latest = workflow.get()
                report.update(workflow_stage=latest["stage"], workflow_run_id=latest["id"],
                              planning_run_id=latest["planning_run_id"],
                              metrics=WorkflowRecords(workflow.store, latest["id"]).summary())
                save_record(directory / "final-run.json", latest)
            except (HarnessError, OSError) as exc:
                report.update(status_error=str(exc), technical_verification_passed=False)
        report["fixture_preserved"] = snapshot(fixture) == fixture_before
        report["technical_verification_passed"] &= report["fixture_preserved"]
        save_record(directory / "report.json", report)
        print(json.dumps({k: v for k, v in report.items() if k not in {
            "stages", "harness_source", "commands", "fixture_hashes", "final_file_hashes", "traceback"}},
            ensure_ascii=True, indent=2), flush=True)
    return 0 if report["technical_verification_passed"] else 1


if __name__ == "__main__":
    raise SystemExit(main())
