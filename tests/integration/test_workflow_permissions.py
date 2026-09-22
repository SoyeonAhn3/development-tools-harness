import json
from pathlib import Path
import shutil
import subprocess
import time
import uuid

import psutil
import pytest

from development_harness.appcontainer_probe import Listeners, TOKEN
from development_harness.codex_adapter import default_model, executable, SUPPORTED_VERSIONS
from development_harness.isolated_validation import IsolatedValidator
from development_harness.model import HarnessError
from development_harness.store import default_home
from development_harness.workers import CodexWorker


CHECK = {"argv": ["{python}", "-m", "pytest", "-q"], "kind": "pytest", "timeout": 30}


@pytest.fixture(scope="module")
def validation_environment():
    root = default_home().parent / "t2-tests" / uuid.uuid4().hex[:12]
    root.mkdir(parents=True)
    validator = IsolatedValidator(root / "validator")
    report = validator.verify()
    assert report["ready"] and report["checks"]["standard_user"], report
    return root, validator


@pytest.mark.parametrize("text,expected,count", [
    ("def test_pass():\n    assert 2 + 2 == 4\n", "passed", 1),
    ("def test_failure():\n    assert False\n", "failed", 1),
    ("import pytest\n@pytest.mark.skip(reason='required case skipped')\ndef test_skip():\n    pass\n", "no_tests", 0),
    ("def helper_only():\n    pass\n", "no_tests", 0),
    ("import missing_required_test_dependency\n", "unverified", 1),
])
def test_isolated_pytest_classifies_actual_results(validation_environment, text, expected, count):
    root, validator = validation_environment
    project = root / ("result-" + uuid.uuid4().hex[:8])
    project.mkdir()
    (project / "test_case.py").write_text(text, encoding="utf-8")
    result = validator.run(CHECK, project)
    assert result["outcome"] == expected, result
    assert result["tests"] == count, result
    assert result["container"]["delete_hresult"] == 0
    assert (project / "test_case.py").read_text(encoding="utf-8") == text


def test_actual_isolated_check_uses_durable_controller_attempt(validation_environment):
    from development_harness.files import snapshot
    from development_harness.model import digest
    from development_harness.store import Store
    from development_harness.workflow_records import WorkflowRecords

    root, validator = validation_environment
    project = root / "journal-project"
    project.mkdir()
    (project / "test_case.py").write_text("def test_actual():\n    assert 3 * 2 == 6\n", encoding="utf-8")
    store = Store(project, root / "journal-runtime")
    policy = {"validation": [CHECK]}
    store.save({"id": "isolated-journal", "kind": "workflow", "stage": "execution_ready",
                "plan_hash": "test-plan", "policy_hash": digest(policy), "policy": policy,
                "expected": snapshot(project), "attempts": [], "findings": {}, "waits": [],
                "tasks": [{"id": "T1", "requirements": ["R1"], "paths": ["test_case.py"]}]}, "created", new=True)
    records = WorkflowRecords(store, "isolated-journal")
    attempt = records.prepare_attempt("T1", "validation", digest(snapshot(project)))
    attempt["check_hash"] = digest(CHECK)
    records.lifecycle(attempt, "prepared")
    def launched(evidence):
        attempt.update(evidence)
        records.lifecycle(attempt, "process_registered")
        assert store.get()["attempts"][0]["process"] == evidence["process"]
    result = validator.run(CHECK, project, launched=launched, attempt_id=attempt["id"])
    attempt.update(result)
    records.lifecycle(attempt, "finished")
    stored = store.get()["attempts"][0]
    assert stored["outcome"] == "passed", stored
    assert stored["tests"] == 1
    assert json.loads(Path(stored["record"]).read_text(encoding="utf-8"))["id"] == attempt["id"]
    assert records.summary()["ai_dispatch_attempts"] == 0


def test_actual_pytest_and_child_cannot_change_protected_files_or_connect(validation_environment):
    root, validator = validation_environment
    project = root / "permission-project"
    project.mkdir()
    controller = root / "control"
    controller.mkdir()
    paths = {"approval": controller / "state.sqlite3", "runner": controller / "runner.py",
             "environment_file": project / "config/production.env",
             "git": project / ".git/config", "policy": project / "harness-project.json", "unrelated": root / "unrelated.txt"}
    for path in paths.values():
        path.parent.mkdir(parents=True, exist_ok=True)
        path.write_text("protected original\n", encoding="utf-8")
    paths["installed_package"] = validator.runtime / "Lib/site-packages/pytest/__init__.py"
    before = {name: path.read_bytes() for name, path in paths.items()}
    payload = Path(__file__).parents[2] / "src/development_harness/appcontainer_probe_payload.py"
    shutil.copy2(payload, project / "permission_payload.py")
    with Listeners() as listeners:
        assert all(listeners.controls("host:before").values())
        spec = {"role": "validation", "paths": {k: str(v) for k, v in paths.items()}, "endpoints": listeners.endpoints}
        (project / "probe.json").write_text(json.dumps(spec), encoding="utf-8")
        (project / "test_permissions.py").write_text('''import json,os,subprocess,sys
from pathlib import Path
import permission_payload as payload
def test_permissions():
    temporary=Path(os.environ['TEMP'])
    spec=json.loads(Path('probe.json').read_text())
    spec['paths']['scratch']=str(temporary/'allowed.txt')
    Path(spec['paths']['scratch']).write_text('initial')
    spec['paths']['copied_source']=str(Path(__file__))
    input_path=temporary/'child-input.json'
    input_path.write_text(json.dumps(spec))
    parent=payload.observe(spec,'parent')
    child=subprocess.run([sys.executable,'-I','-B',str(Path(payload.__file__)),str(input_path),'--child'],capture_output=True,text=True,timeout=12)
    assert child.returncode==0,child.stderr
    records={'parent':parent,'child':json.loads(child.stdout)}
    (temporary/'permissions.json').write_text(json.dumps(records))
    for record in records.values():
        assert record['token']=={'appcontainer':True,'capability_count':0,'elevated':False}
        for name,value in record['writes'].items():
            assert value['outcome']==('written' if name=='scratch' else 'denied'),(name,value)
        for name,value in record['reads'].items():
            assert value==('read' if name in {'scratch','copied_source','installed_package'} else 'denied'),(name,value)
        assert all(v['outcome']=='denied' for v in record['networks'].values())
''', encoding="utf-8")
        result = validator.run(CHECK, project)
        assert result["outcome"] == "passed", result
        assert all(listeners.controls("host:after").values())
        assert len(listeners.received) == 8
        assert all(value.startswith("host:") for value in listeners.received)
    for name, path in paths.items():
        assert path.read_bytes() == before[name]
    evidence = json.loads((Path(result["copied_project"]).parent / "tmp/permissions.json").read_text())
    assert evidence["parent"]["pid"] == result["process"]["pid"]
    assert evidence["child"]["pid"] != evidence["parent"]["pid"]
    assert evidence["child"]["token"] == TOKEN
    assert not (Path(result["copied_project"]) / "harness-project.json").exists()
    assert not (Path(result["copied_project"]) / "config/production.env").exists()


def test_isolated_pytest_deadline_kills_descendant(validation_environment):
    root, validator = validation_environment
    project = root / "timeout-project"
    project.mkdir()
    (project / "test_wait.py").write_text('''import os,subprocess,sys,time
def test_wait():
    code="import os,time;from pathlib import Path;Path(os.environ['TEMP'],'child.pid').write_text(str(os.getpid()));time.sleep(60)"
    subprocess.Popen([sys.executable,'-I','-B','-c',code],creationflags=subprocess.CREATE_NO_WINDOW)
    time.sleep(60)
''', encoding="utf-8")
    result = validator.run(dict(CHECK, timeout=3), project)
    assert result["outcome"] == "interrupted", result
    assert result["ended"] is result["duration"] is None
    child = int((Path(result["copied_project"]).parent / "tmp/child.pid").read_text())
    for _ in range(30):
        if not psutil.pid_exists(child):
            break
        time.sleep(0.1)
    assert not psutil.pid_exists(child)
    assert not psutil.pid_exists(result["process"]["pid"])


def test_user_changes_invalidate_copied_test_evidence(validation_environment):
    root, validator = validation_environment
    project = root / "edited-project"
    project.mkdir()
    path = project / "test_case.py"
    path.write_text("def test_ok():\n    assert True\n")
    result = validator.run(CHECK, project, launched=lambda _: path.write_text("user edit\n"))
    assert result["outcome"] == "unverified", result
    assert "Unexpected file changes" in result["reason"]
    assert path.read_text() == "user edit\n"


def test_recording_failure_never_resumes_project_code(validation_environment):
    root, validator = validation_environment
    project = root / "dispatch-project"
    project.mkdir()
    (project / "test_case.py").write_text("import os\nfrom pathlib import Path\nPath(os.environ['TEMP'],'ran.txt').write_text('unsafe')\ndef test_ok():\n    pass\n")
    def failure(_):
        raise RuntimeError("synthetic persistence failure")
    result = validator.run(CHECK, project, launched=failure)
    assert result["outcome"] == "unverified", result
    assert not (Path(result["copied_project"]).parent / "tmp/ran.txt").exists()
    assert not psutil.pid_exists(result["process"]["pid"])


@pytest.mark.parametrize("role", ["developer", "reviewer"])
def test_actual_selected_cli_role_boundary_rejects_forced_tools(role):
    try:
        selected = executable()
    except HarnessError as exc:
        pytest.skip(str(exc))
    version = subprocess.run([str(selected), "--version"], capture_output=True, text=True, timeout=10).stdout.strip()
    if version not in SUPPORTED_VERSIONS:
        pytest.skip("Installed CLI contract needs review")
    directory = default_home().parent / "t2-role-probes" / uuid.uuid4().hex[:12] / role
    adapter = CodexWorker(role, default_model(), directory, codex_path=selected)
    report = adapter.verify()
    assert report["ready"]
    assert set(report["rejected_tools"]) >= {"exec_command", "shell", "apply_patch", "web.run", "spawn_agent"}
    assert report["probe_actual_ai_calls"] == 0
    assert not (directory / "forbidden-tool-write.txt").exists()
