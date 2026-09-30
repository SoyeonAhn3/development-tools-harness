"""Disposable T8 proofs. No live AI requests, user acceptance or self-development."""

import argparse
import json
import os
from pathlib import Path
import shutil
import subprocess
import sys
import uuid

from .appcontainer_probe import TOKEN
from .files import snapshot
from .frozen_entry import file_hash, guard_paths, inspect_runner
from .isolated_validation import IsolatedValidator
from .model import HarnessError
from .store import Store, default_home
from .validation import pytest_result
from .worker_contract import save_record


PERMISSION_PAYLOAD = '''import json, os, sys
from pathlib import Path
from development_harness.appcontainer_probe_payload import token

def observe(paths):
    result = {'pid': os.getpid(), 'token': token(), 'writes': {}}
    for name, value in paths.items():
        try:
            with Path(value).open('ab') as stream:
                stream.write(b'forbidden-t8-write')
            result['writes'][name] = 'written'
        except PermissionError:
            result['writes'][name] = 'denied'
        except OSError as exc:
            result['writes'][name] = 'error: ' + str(exc)
    return result

if __name__ == '__main__':
    print(json.dumps(observe(json.loads(Path(sys.argv[1]).read_text()))))
'''

PERMISSION_TEST = '''import json, os, subprocess, sys
from pathlib import Path
import development_harness.store as store_module
from development_harness.store import Store
import permission_payload

def test_b_storage_and_child_permissions():
    work = Path.cwd()
    scratch = Path(os.environ['TEMP'])
    assert Path(store_module.__file__).resolve().is_relative_to(work / 'src')
    paths = json.loads(Path('probe.json').read_text())
    parent = permission_payload.observe(paths)
    # -I prevents inherited/project imports; explicitly select this tested B copy.
    code = "import sys;sys.path[:0]=sys.argv[1:3];import permission_payload,json;from pathlib import Path;print(json.dumps(permission_payload.observe(json.loads(Path(sys.argv[3]).read_text()))))"
    child = subprocess.run([sys.executable, '-I', '-B', '-c', code, str(work / 'src'), str(work), str(work / 'probe.json')],
                           capture_output=True, text=True, timeout=15)
    assert child.returncode == 0, child.stderr
    records = {'parent': parent, 'child': json.loads(child.stdout), 'module_origin': store_module.__file__}
    db = Store(work, scratch / 'b-state')
    db.save({'id': 'b-temporary-test', 'stage': 'accepted'}, 'temporary-test', new=True)
    records['temporary_database'] = db.get('b-temporary-test')['stage'] == 'accepted'
    records['temporary_database_path'] = str(db.path)
    (scratch / 'permissions.json').write_text(json.dumps(records))
    assert records['temporary_database']
    assert records['parent']['pid'] != records['child']['pid']
    for record in (records['parent'], records['child']):
        assert record['token'] == {'appcontainer': True, 'capability_count': 0, 'elevated': False}
        assert all(value == 'denied' for value in record['writes'].values()), record
'''


def verify_permissions(repository, runner, directory):
    """Execute B imports/tests, targeting only a newly created protected A replica."""
    repository, runner, directory = map(Path, (repository, runner, directory))
    guard_paths(runner, repository, directory)
    before = inspect_runner(runner)
    directory.mkdir(parents=True, exist_ok=False)
    replica = directory / "protected/A"
    shutil.copytree(runner, replica)
    inspect_runner(replica)
    project = directory / "B"
    shutil.copytree(repository / "src/development_harness", project / "src/development_harness",
                    ignore=shutil.ignore_patterns("__pycache__", "*.pyc"))
    protected_project = directory / "protected/project"
    protected_project.mkdir()
    store = Store(protected_project, directory / "protected/state")
    store.save({"id": "protected-approval", "stage": "accepted", "approval": {"fixture": True}},
               "synthetic-approval", new=True)
    log = directory / "protected/execution.log"
    log.write_text("Synthetic controller log; no active records.\n", encoding="utf-8")
    paths = {"launcher": replica / "run.py", "manifest": replica / "runner-manifest.json",
             "python": replica / "runtime/python.exe", "adapter": replica / "tools/codex.exe",
             "package": replica / "runtime/Lib/site-packages/development_harness/store.py",
             "roles": replica / "runtime/Lib/site-packages/development_harness/workers.py",
             "dependency": replica / "runtime/Lib/site-packages/pytest/__init__.py",
             "policy": replica / "policy.json", "approval": store.path, "log": log}
    hashes = {name: file_hash(path) for name, path in paths.items()}
    save_record(project / "probe.json", {name: str(path) for name, path in paths.items()})
    (project / "permission_payload.py").write_text(PERMISSION_PAYLOAD, encoding="utf-8")
    (project / "test_permissions.py").write_text(PERMISSION_TEST, encoding="utf-8")
    validator = IsolatedValidator(directory / "validator")
    validator.verify()
    result = validator.run({"argv": ["{python}", "-m", "pytest", "-q"], "kind": "pytest", "timeout": 45}, project)
    save_record(directory / "validation.json", result)
    if result["outcome"] != "passed" or result["tests"] != 1:
        raise HarnessError("B isolation proof failed; inspect " + str(directory / "validation.json"))
    records = json.loads((Path(result["copied_project"]).parent / "tmp/permissions.json").read_text(encoding="utf-8"))
    if any(records[g]["token"] != TOKEN or set(records[g]["writes"]) != set(paths) or
           any(v != "denied" for v in records[g]["writes"].values()) for g in ("parent", "child")):
        raise HarnessError("B process/descendant denial evidence is incomplete.")
    if (records["parent"]["pid"] != result["process"]["pid"] or not records["temporary_database"] or
            hashes != {name: file_hash(path) for name, path in paths.items()} or
            inspect_runner(replica) != before or inspect_runner(runner) != before):
        raise HarnessError("Protected content or process evidence changed during B validation.")
    records.update(passed=True, runner_artifact=before["artifact_id"], protected_paths={k: str(v) for k, v in paths.items()},
                   protected_hashes=hashes, validation_record=result["record"], junit=result["junit"],
                   b_sources=snapshot(project / "src"), scope="Actual B code/test and child; disposable A/storage replica")
    save_record(directory / "proof.json", records)
    return records


INSTALLED_TEST = '''import json, subprocess, sys
from pathlib import Path
from development_harness.frozen_entry import inspect_runner
from test_workflow import admitted_factory, isolated_factory, reviewer, scripted_workers
from test_workflow_resume import crash

RUNNER = Path(json.loads(Path(__file__).with_name('runner.json').read_text())['runner'])

def test_installed_module_origins():
    assert Path(sys.executable).resolve() == RUNNER / 'runtime/python.exe'
    for name, module in list(sys.modules.items()):
        if name.startswith('development_harness') and getattr(module, '__file__', None):
            assert Path(module.__file__).resolve().is_relative_to(RUNNER / 'runtime/Lib/site-packages'), name
    inspect_runner(RUNNER)

def test_frozen_public_cli_recovers_then_validates(admitted_factory, isolated_factory):
    workflow = admitted_factory(tasks=1)
    approval = workflow.get()['approval']
    interrupted = crash(workflow, 'response_saved')
    original_attempt = interrupted['attempts'][0]['id']
    command = [sys.executable, '-I', '-B', str(RUNNER / 'run.py'), '--project', str(workflow.project), '--state-dir', str(workflow.store.home)]
    def call(*args):
        result = subprocess.run(command + list(args), capture_output=True, text=True, timeout=120)
        assert result.returncode == 0, result.stdout + result.stderr
        return json.loads(result.stdout)
    call('workflow-status')
    call('workflow-resume', '--steps', '1')
    assert len(workflow.get()['attempts']) == 1
    assert workflow.get()['execution']['stage'] == 'validation'
    call('workflow-resume', '--steps', '1')
    assert workflow.get()['execution']['stage'] == 'review'
    assert workflow.get()['attempts'][1]['backend'] == 'appcontainer'
    result = workflow.resume(worker_factory=scripted_workers([reviewer()]), validator_factory=isolated_factory)
    assert result['stage'] == 'technically_complete', result.get('reason')
    assert result['approval'] == approval
    assert result['attempts'][0]['id'] == original_attempt
    assert len([a for a in result['attempts'] if a['role'] == 'developer']) == 1
    report = call('workflow-report')
    assert report['stage'] == 'technically_complete'
    assert not report['acceptance']['accepted']
    inspect_runner(RUNNER)
'''


def verify_installed_workflow(repository, runner, directory):
    repository, runner, directory = map(Path, (repository, runner, directory))
    guard_paths(runner, repository, directory)
    directory.mkdir(parents=True, exist_ok=False)
    tests = directory / "tests"
    tests.mkdir()
    names = ["test_workflow.py", "test_workflow_resume.py", "test_workflow_admission_cli.py",
             "test_workflow_permissions.py", "test_isolated_temporary_directories.py"]
    for name in names:
        shutil.copy2(repository / "tests/integration" / name, tests / name)
    (tests / "test_installed_t8.py").write_text(INSTALLED_TEST, encoding="utf-8")
    save_record(tests / "runner.json", {"runner": str(runner)})
    selected = [str(tests / "test_installed_t8.py"),
                str(tests / "test_workflow.py") + "::test_ordered_tasks_preserve_approval_and_validate_final_content",
                str(tests / "test_workflow_resume.py") + "::test_saved_developer_result_is_reused_without_a_second_developer_call",
                str(tests / "test_workflow_resume.py") + "::test_running_real_isolated_validation_is_retried_then_final_content_is_revalidated",
                str(tests / "test_workflow_admission_cli.py") + "::test_cli_prepare_status_approve_cancel_preserve_planning_and_project",
                str(tests / "test_workflow_admission_cli.py") + "::test_cli_plan_approval_does_not_imply_execution_authorization",
                str(tests / "test_isolated_temporary_directories.py")]
    env = os.environ | {"PYTHONDONTWRITEBYTECODE": "1", "PYTEST_DISABLE_PLUGIN_AUTOLOAD": "1", "PYTEST_ADDOPTS": ""}
    for name in ("PYTHONPATH", "PYTHONHOME", "PYTEST_PLUGINS"):
        env.pop(name, None)
    junit = directory / "pytest.xml"
    # The fixtures append project hashes and attempt IDs. Keep this temporary
    # root short even when the caller chooses a deeply nested evidence location.
    temporary = default_home().parent.parent / "harness-t8-tmp" / uuid.uuid4().hex[:10]
    temporary.parent.mkdir(parents=True, exist_ok=True)
    argv = [str(runner / "runtime/python.exe"), "-I", "-B", "-m", "pytest", "-q", *selected,
            "--basetemp", str(temporary), "--junitxml", str(junit), "-p", "no:cacheprovider"]
    with (directory / "stdout.log").open("wb") as out, (directory / "stderr.log").open("wb") as err:
        result = subprocess.run(argv, cwd=directory, env=env, stdout=out, stderr=err, timeout=600,
                                creationflags=subprocess.CREATE_NO_WINDOW)
    outcome, count = pytest_result(junit)
    record = {"argv": argv, "exit_code": result.returncode, "outcome": outcome, "tests": count,
              "junit": str(junit), "junit_sha256": file_hash(junit), "fixtures": snapshot(tests),
              "actual_ai_calls": 0, "role_transport": "Deterministic local subprocess fixtures",
              "validation": "Actual AppContainer; installed A CLI and process-crash recovery"}
    save_record(directory / "proof.json", record)
    if result.returncode or outcome != "passed":
        raise HarnessError("Installed workflow/resume verification failed; inspect " + str(directory / "stdout.log"))
    inspect_runner(runner)
    return record


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--repository", required=True)
    parser.add_argument("--runner", required=True)
    parser.add_argument("--directory", required=True)
    args = parser.parse_args()
    repository, runner, directory = (Path(value).resolve() for value in (args.repository, args.runner, args.directory))
    guard_paths(runner, repository, directory)
    directory.mkdir(parents=True, exist_ok=False)
    report = {"passed": False, "actual_ai_calls": 0, "self_development": False, "phase3_accepted": False,
              "directory": str(directory), "runner": str(runner), "stages": {}}
    def stage(name, value):
        report["stages"][name] = value
        save_record(directory / "report.json", report)
        print(json.dumps({"stage": name, "directory": str(directory)}), flush=True)
    try:
        manifest = inspect_runner(runner)
        if Path(__file__).resolve().parent != runner / "runtime/Lib/site-packages/development_harness":
            raise HarnessError("Run T8 verification with the frozen runner's Python -I -B -m development_harness.fixed_runner_verify.")
        stage("manifest", {"artifact_id": manifest["artifact_id"], "sha256": file_hash(runner / "runner-manifest.json")})
        stage("permissions", verify_permissions(repository, runner, directory / "permissions"))
        from .codex_adapter import default_model
        from .workers import CodexWorker
        roles = {}
        for role in ("developer", "reviewer"):
            worker = CodexWorker(role, default_model(), directory / ("role-" + role), codex_path=runner / "tools/codex.exe")
            roles[role] = worker.verify()
            if not roles[role].get("ready") or roles[role].get("probe_actual_ai_calls") != 0:
                raise HarnessError("Pinned role boundary verification is incomplete.")
        stage("roles", roles)
        stage("installed_workflow", verify_installed_workflow(repository, runner, directory / "installed-workflow"))
        acceptance_path = repository / "Phase/Evidence/Phase3_Example_Acceptance.json"
        acceptance = json.loads(acceptance_path.read_text(encoding="utf-8"))
        if acceptance["status"] != "Accepted and completed" or not acceptance["acceptance_status"]["accepted"]:
            raise HarnessError("T7 external example acceptance is required.")
        accepted_report = Path(os.path.expandvars(acceptance["accepted_report"]["path"]))
        if file_hash(accepted_report) != acceptance["accepted_report"]["sha256"]:
            raise HarnessError("T7 accepted report differs from its preserved evidence.")
        stage("t7_acceptance", {"path": str(acceptance_path), "sha256": file_hash(acceptance_path),
                               "accepted_report_sha256": file_hash(accepted_report), "new_acceptance": False})
        if inspect_runner(runner) != manifest:
            raise HarnessError("Frozen runner changed during verification.")
        report["passed"] = True
        stage("complete", {"runner_unchanged": True, "artifact_id": manifest["artifact_id"]})
        return 0
    except Exception as exc:
        stage("failure", {"error": str(exc)})
        raise


if __name__ == "__main__":
    raise SystemExit(main())
