"""Real Windows process lifetime and read-only recovery ownership checks."""

import json
from pathlib import Path
import subprocess
import sys
import time

import psutil
import pytest

from development_harness.model import HarnessError
from development_harness.processes import Job, ProjectLock, alive, default_home, ensure_stopped, identity
from development_harness.runner import Harness
from test_workflow_permissions import validation_environment


def until(predicate, timeout=10):
    deadline = time.monotonic() + timeout
    while time.monotonic() < deadline:
        if predicate():
            return
        time.sleep(0.025)
    assert predicate(), "Actual process state did not settle before the deadline"


CONTROLLER = r'''
import hashlib, json, os, sys, time
from pathlib import Path
from development_harness import codex_adapter
from development_harness.codex_adapter import CodexPlanner
from development_harness.processes import Job, identity

directory = Path(sys.argv[1])
boundary = sys.argv[2]
adapter = CodexPlanner.__new__(CodexPlanner)
adapter.exe, adapter.model, adapter.directory = Path(sys.executable), 'fixture', directory
adapter.policy = {'binary_hash': hashlib.sha256(adapter.exe.read_bytes()).hexdigest()}
target = r"""
import json, subprocess, sys, time
from pathlib import Path
import psutil
sys.stdin.read()
Path('target-started').write_text('started')
if sys.argv[1] == 'running':
    child = subprocess.Popen([sys.executable, '-c', 'import time; time.sleep(60)'],
                             creationflags=subprocess.CREATE_NO_WINDOW)
    Path('child.json').write_text(json.dumps({'pid': child.pid, 'created': psutil.Process(child.pid).create_time()}))
    time.sleep(60)
print(json.dumps({'type': 'item.completed', 'item': {'type': 'agent_message', 'text': '{}'}}))
print(json.dumps({'type': 'turn.completed'}))
"""
adapter.arguments = lambda _: [sys.executable, '-c', target, boundary]
if boundary in {'before_assign', 'after_assign'}:
    original = Job.assign
    def interrupted_assign(job, pid):
        if boundary == 'after_assign':
            original(job, pid)
        (directory / 'observed.json').write_text(json.dumps({'process': identity(pid), 'containment': job.record}))
        os._exit(99)
    Job.assign = interrupted_assign
def observe(record, phase):
    (directory / 'observed.json').write_text(json.dumps(record))
    if phase == boundary:
        os._exit(99)
adapter.lifecycle = observe
adapter.generate('inert fixture input', {}, {'id': 'attempt'}, lambda _: None, timeout=30)
'''


@pytest.mark.parametrize("boundary", ["before_assign", "after_assign", "process_registered", "dispatch_intent"])
def test_controller_death_before_input_never_starts_target_or_leaves_gate(tmp_path, boundary):
    result = subprocess.run([sys.executable, "-c", CONTROLLER, str(tmp_path), boundary],
                            capture_output=True, timeout=15, creationflags=subprocess.CREATE_NO_WINDOW)
    assert result.returncode == 99, result.stdout + result.stderr
    observed = json.loads((tmp_path / "observed.json").read_text())
    until(lambda: not alive(observed["process"]))
    assert not (tmp_path / "target-started").exists()
    ensure_stopped([observed])


def test_forced_controller_death_stops_actual_worker_and_descendant(tmp_path):
    controller = subprocess.Popen([sys.executable, "-c", CONTROLLER, str(tmp_path), "running"],
                                  stdout=subprocess.PIPE, stderr=subprocess.PIPE,
                                  creationflags=subprocess.CREATE_NO_WINDOW)
    try:
        until(lambda: (tmp_path / "child.json").exists())
        child = json.loads((tmp_path / "child.json").read_text())
        observed = json.loads((tmp_path / "observed.json").read_text())
        assert Job.active_processes(observed["containment"]["name"]) >= 3
        with pytest.raises(HarnessError, match="still active"):
            ensure_stopped([observed])
        controller.kill()
        controller.communicate(timeout=10)
        until(lambda: not alive(observed["process"]) and not alive(child))
        ensure_stopped([observed])
    finally:
        if controller.poll() is None:
            controller.kill()
            controller.communicate(timeout=10)


@pytest.mark.parametrize("boundary", ["created", "registered"])
def test_appcontainer_controller_death_before_resume_leaves_no_suspended_orphan(validation_environment, boundary):
    root, validator = validation_environment
    work = root / ("crash-" + boundary)
    scratch = work / "tmp"
    scratch.mkdir(parents=True)
    target = work / "target.py"
    target.write_text("from pathlib import Path\nPath('tmp/target-started').write_text('unexpected')\n")
    controller = r'''
import ctypes, json, os, sys
from pathlib import Path
from development_harness.processes import identity
from development_harness.windows_appcontainer import AppContainer, _Process
root, runtime, work = map(Path, sys.argv[1:4])
boundary = sys.argv[4]
container = AppContainer(root)
with container:
    (work / 'profile.txt').write_text(container.name)
    container.grant(runtime)
    container.grant(work)
    container.grant(work / 'tmp', write=True)
    if boundary == 'created':
        original = container.api.CreateProcessW
        def interrupted_create(*arguments):
            result = original(*arguments)
            if result:
                process = ctypes.cast(arguments[-1], ctypes.POINTER(_Process)).contents
                (work / 'observed.json').write_text(json.dumps({'process': identity(process.pid)}))
                os._exit(99)
            return result
        container.api.CreateProcessW = interrupted_create
    def launched(record):
        (work / 'observed.json').write_text(json.dumps(record))
        os._exit(99)
    container.run([runtime / 'python.exe', '-I', '-B', work / 'target.py'], work,
                  work / 'process', scratch=work / 'tmp', launched=launched)
'''
    try:
        result = subprocess.run([sys.executable, "-c", controller, str(root), str(validator.runtime), str(work), boundary],
                                capture_output=True, timeout=25, creationflags=subprocess.CREATE_NO_WINDOW)
        assert result.returncode == 99, result.stdout + result.stderr
        observed = json.loads((work / "observed.json").read_text())
        until(lambda: not alive(observed["process"]))
        assert not (scratch / "target-started").exists()
        if boundary == "registered":
            ensure_stopped([observed])
    finally:
        if (work / "profile.txt").exists():
            from development_harness.windows_appcontainer import _Api
            assert _Api().DeleteAppContainerProfile((work / "profile.txt").read_text()) == 0


def test_dead_root_with_live_named_job_descendant_blocks_without_killing(tmp_path):
    job = Job()
    source = ("import json, subprocess, sys\n"
              "import psutil\n"
              "sys.stdin.read()\n"
              "child = subprocess.Popen([sys.executable, '-c', 'import time; time.sleep(60)'])\n"
              "print(json.dumps({'pid':child.pid,'created':psutil.Process(child.pid).create_time()}), flush=True)\n")
    worker = subprocess.Popen([sys.executable, "-c", source], stdin=subprocess.PIPE,
                              stdout=subprocess.PIPE, stderr=subprocess.PIPE,
                              creationflags=subprocess.CREATE_NO_WINDOW)
    try:
        job.assign(worker.pid)
        parent = identity(worker.pid)
        worker.stdin.close()
        child = json.loads(worker.stdout.readline())
        worker.wait(timeout=10)
        assert not alive(parent) and alive(child)
        with pytest.raises(HarnessError, match="descendants are still active"):
            ensure_stopped([{"process": parent, "containment": job.record}])
        assert alive(child)
        job.close()
        until(lambda: not alive(child))
        ensure_stopped([{"process": parent, "containment": job.record}])
    finally:
        job.close()
        if worker.poll() is None:
            worker.kill()
            worker.wait(timeout=10)
        worker.stdout.close()
        worker.stderr.close()


def test_pid_reuse_and_finished_legacy_history_do_not_kill_current_process():
    reused = identity() | {"created": identity()["created"] - 10}
    ensure_stopped([{"process": reused, "journal_phases": {"finished": 1}}])
    job = Job()
    job.close()
    ensure_stopped([{"process": reused, "containment": job.record}])
    assert alive(identity())
    with pytest.raises(HarnessError, match="containment evidence"):
        ensure_stopped([{"process": reused, "journal_phases": {"process_registered": 1}}])
    with pytest.raises(HarnessError, match="still active"):
        ensure_stopped([{"process": identity(), "journal_phases": {"finished": 1}}])
    assert alive(identity())


def test_process_inspection_uncertainty_and_malformed_identity_block(monkeypatch):
    current = identity()
    monkeypatch.setattr(psutil, "Process", lambda _: (_ for _ in ()).throw(psutil.AccessDenied()))
    with pytest.raises(HarnessError, match="Cannot inspect"):
        ensure_stopped([{"process": current}])
    with pytest.raises(HarnessError, match="Invalid recorded process identity"):
        ensure_stopped([{"process": {"pid": current["pid"]}}])
    with pytest.raises(HarnessError, match="no recorded process identity"):
        ensure_stopped([{"dispatch_status": "uncertain"}])


@pytest.mark.parametrize("damage", ["missing", "corrupt", "missing_table"])
def test_alternate_state_cannot_claim_missing_or_unreadable_previous_database(workspace, tmp_path, damage):
    harness, _, plan, _ = workspace
    harness.prepare(plan)
    alternate = Harness(harness.project, tmp_path / "alternate")
    record = default_home() / "ownership" / (harness.store.project_id + ".json")
    before = record.read_bytes()
    if damage == "missing":
        harness.store.path.unlink()
    elif damage == "corrupt":
        harness.store.path.write_bytes(b"not a SQLite database")
    else:
        with harness.store.connect() as db:
            db.execute("DROP TABLE events")
            db.execute("DROP TABLE runs")
    with pytest.raises(HarnessError, match="ownership database"):
        with ProjectLock(alternate.store):
            pytest.fail("Alternate controller acquired an unverified ownership record")
    assert record.read_bytes() == before
    assert alternate.store.active() is None


def test_recovery_guard_does_not_acquire_a_live_other_owner(workspace):
    harness, _, _, _ = workspace
    with ProjectLock(harness.store):
        with pytest.raises(HarnessError, match="Another process owns"):
            with ProjectLock(harness.store):
                pytest.fail("A second project owner acquired the same lock")


def test_empty_prepared_attempt_is_safe_and_corrupt_containment_is_not():
    ensure_stopped([{"dispatch_status": "not_sent", "journal_phases": {"prepared": 1}}])
    with pytest.raises(HarnessError, match="Invalid recorded process containment"):
        ensure_stopped([{"containment": {"kind": "windows_job_v1", "name": "another-application"}}])
