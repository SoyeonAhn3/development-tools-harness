"""Explicit live P3-T2 component check on a fresh, disposable fixture copy.

Run with the harness Python and --live. This does not approve/execute a project
plan, implement T3/T4 orchestration or count as the T7 accepted workflow example.
"""

import argparse
import hashlib
import json
from pathlib import Path
import shutil
import uuid

from development_harness.codex_adapter import default_model
from development_harness.files import snapshot
from development_harness.isolated_validation import IsolatedValidator, review_evidence
from development_harness.model import HarnessError, digest
from development_harness.store import default_home
from development_harness.worker_contract import TaskScope, apply_proposal, save_record
from development_harness.workers import CodexWorker


REQUIREMENTS = {
    "R1": "Preserve python cli.py 3 -> exit 0, stdout '6\\n', no stderr; and input 0 -> '0\\n'.",
    "R2": "Reject negative integers with nonzero exit, empty stdout and clear stderr explaining nonnegative input is required.",
    "R3": "Preserve argparse rejection of missing or non-integer arguments.",
    "R4": "Retain existing positive/zero command tests and add meaningful negative-input command tests.",
    "R5": "Only change cli.py and test_cli.py, using existing standard library and pytest; no installation, network, UI or policy changes.",
}
CHECK = {"argv": ["{python}", "-m", "pytest", "-q"], "kind": "pytest", "timeout": 45}
CONTROLLER_CHECKS = '''import subprocess,sys
import pytest
@pytest.mark.parametrize('args,stdout,success', [(['3'],'6\\n',True),(['0'],'0\\n',True),(['-1'],'',False),(['not-an-int'],'',False),([],'',False)])
def test_controller_requirement(args,stdout,success):
    result=subprocess.run([sys.executable,'cli.py',*args],capture_output=True,text=True,timeout=5)
    assert (result.returncode==0)==success
    assert result.stdout==stdout
    assert (result.stderr=='')==success
'''


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--live", action="store_true", help="Explicitly allow two real role calls on the disposable fixture")
    parser.add_argument("--model")
    parser.add_argument("--codex-path")
    args = parser.parse_args()
    if not args.live:
        parser.error("Use --live for this explicit component test; it makes real Developer and Reviewer calls.")
    model = args.model or default_model()
    directory = default_home().parent / "t2-live" / uuid.uuid4().hex[:12]
    directory.mkdir(parents=True)
    fixture = Path(__file__).resolve().parents[1] / "tests/fixtures/workflow_project"
    fixture_before = snapshot(fixture)
    project = directory / "project"
    shutil.copytree(fixture, project)
    report = {"scope": "P3-T2 disposable component verification only", "directory": str(directory),
              "passed": False, "workflow_execution_enabled": False, "plan_approval_created": False,
              "actual_ai_call_attempts": 0, "model": model, "stages": {}}

    def stage(name, data):
        report["stages"][name] = data
        save_record(directory / "report.json", report)
        print(json.dumps({"stage": name, "directory": str(directory)}, ensure_ascii=True), flush=True)

    try:
        validator = IsolatedValidator(directory / "validator")
        permissions = validator.verify()
        stage("permissions", {"ready": permissions["ready"], "directory": permissions["evidence_directory"]})
        baseline = validator.run(CHECK, project)
        stage("baseline", baseline)
        if baseline["outcome"] != "passed" or baseline["tests"] != 2:
            raise HarnessError("Prepared fixture did not pass its two real baseline tests.")
        scope = TaskScope(project, "T2-EXAMPLE", REQUIREMENTS, ["cli.py", "test_cli.py"], ["spec.md"],
                          instructions="Implement the requested negative-input rejection and tests in this disposable fixture.")
        developer = CodexWorker("developer", model, directory / "developer", codex_path=args.codex_path)
        proposed = developer.invoke(scope, timeout=240)
        stage("developer", proposed)
        applied = apply_proposal(scope, proposed["response"], directory / "patch")
        stage("patch", applied)
        current = scope.refresh()
        validation = validator.run(CHECK, project)
        stage("validation", validation)
        if validation["outcome"] != "passed" or validation["tests"] < 3:
            raise HarnessError("Developer output did not pass the actual retained and added tests.")

        # Independent controller-authored checks never enter the Developer's editable
        # project. They verify the identical application files in a second copy.
        assertions = directory / "assertions"
        shutil.copytree(project, assertions)
        if snapshot(assertions) != current.baseline:
            raise HarnessError("Independent verification copy differs from the resulting application.")
        (assertions / "test_controller_requirements.py").write_text(CONTROLLER_CHECKS, encoding="utf-8")
        independent = validator.run(dict(CHECK, argv=CHECK["argv"] + ["test_controller_requirements.py"]), assertions)
        independent["application_content_version"] = digest(current.baseline)
        independent["controller_test_sha256"] = hashlib.sha256(CONTROLLER_CHECKS.encode()).hexdigest()
        stage("independent_requirements", independent)
        if independent["outcome"] != "passed" or independent["tests"] != 5:
            raise HarnessError("Independent command-level requirements did not all pass.")

        reviewer = CodexWorker("reviewer", model, directory / "reviewer", codex_path=args.codex_path)
        reviewed = reviewer.invoke(current, before=scope.files, validation=[review_evidence(validation)], timeout=240)
        stage("reviewer", reviewed)
        if reviewed["attempt"]["session_id"] == proposed["attempt"]["session_id"]:
            raise HarnessError("Developer and Reviewer unexpectedly reused a session.")
        if reviewed["response"]["verdict"] != "pass":
            raise HarnessError("Independent Reviewer did not pass the resulting implementation.")
        current.check()
        report["fixture_preserved"] = snapshot(fixture) == fixture_before
        report["passed"] = report["fixture_preserved"]
    except Exception as exc:
        report["error"] = str(exc)
    finally:
        attempts = []
        for role in ("developer", "reviewer"):
            path = directory / role / "attempt.json"
            if path.exists():
                attempts.append(json.loads(path.read_text(encoding="utf-8")))
        report["actual_ai_call_attempts"] = sum(a.get("actual_ai_call_attempts", 0) for a in attempts)
        save_record(directory / "report.json", report)
    print(json.dumps({k: v for k, v in report.items() if k != "stages"}, ensure_ascii=True, indent=2), flush=True)
    return 0 if report["passed"] else 1


if __name__ == "__main__":
    raise SystemExit(main())
