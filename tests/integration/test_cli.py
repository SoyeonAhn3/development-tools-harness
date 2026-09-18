import json
import os
from pathlib import Path
import subprocess
import sys
import sysconfig
import time
import venv

import psutil
import pytest

from development_harness.model import HarnessError
from development_harness.processes import alive, identity
from development_harness.runner import Harness


def cli(harness, *args, expected=0):
    result = subprocess.run(
        [sys.executable, "-m", "development_harness", "--project", str(harness.project),
         "--state-dir", str(harness.store.home), *args], capture_output=True, text=True, timeout=45,
    )
    assert result.returncode == expected, result.stdout + result.stderr
    return json.loads(result.stdout) if result.stdout else json.loads(result.stderr)


def running_cli(harness, *args):
    return subprocess.Popen(
        [sys.executable, "-m", "development_harness", "--project", str(harness.project),
         "--state-dir", str(harness.store.home), *args], stdout=subprocess.PIPE, stderr=subprocess.PIPE,
    )


def until(predicate, seconds=15):
    deadline = time.monotonic() + seconds
    while time.monotonic() < deadline:
        value = predicate()
        if value:
            return value
        time.sleep(0.05)
    raise AssertionError("Timed out waiting for expected subprocess state")


def test_help_version_and_bad_command():
    for args, expected in [(["--help"], 0), (["--version"], 0), (["unknown"], 2)]:
        result = subprocess.run([sys.executable, "-m", "development_harness", *args], capture_output=True, timeout=10)
        assert result.returncode == expected
    entry = Path(sys.executable).with_name("dev-harness.exe")
    assert subprocess.run([str(entry), "--version"], capture_output=True, timeout=10).stdout.strip() == b"0.1.0"


def test_cli_full_workflow_fail_fix_review_pause_resume_accept(workspace):
    harness, plan, path, save = workspace
    plan["tasks"][0].update(writes=[{"value.py": "VALUE = 0\n"}, {"value.py": "VALUE = 1\n"}],
                            review=["pass", "changes", "pass"])
    save()
    cli(harness, "prepare", "--plan", str(path))
    assert cli(harness, "run")["stage"] == "awaiting_approval"
    cli(harness, "approve")
    assert cli(harness, "run", "--steps", "1")["stage"] == "validating"
    paused = cli(harness, "status")
    assert paused["attempts"][0]["synthetic"] is True
    ready = cli(harness, "resume")
    assert ready["stage"] == "awaiting_acceptance"
    assert ready["corrections"] == 2
    assert ready["findings"]["task-1:required-change"]["status"] == "resolved"
    validations = [a for a in ready["attempts"] if a["role"] == "validation"]
    assert [a["outcome"] for a in validations] == ["failed", "passed", "passed", "passed"]
    assert all(Path(a["log"]).exists() for a in validations)
    assert all(a.get("tests", 1) > 0 for a in validations)
    assert ready["actual_ai_calls"] == 0
    assert cli(harness, "accept")["stage"] == "accepted"


@pytest.mark.parametrize("test_source,outcome", [
    ("", "no_tests"),
    ("import pytest\n@pytest.mark.skip\ndef test_skip(): pass\n", "no_tests"),
    ("import pytest\ndef test_pass(): pass\n@pytest.mark.skip\ndef test_skip(): pass\n", "unverified"),
])
def test_empty_or_skipped_tests_are_not_success(workspace, test_source, outcome):
    harness, _, path, _ = workspace
    (harness.project / "test_value.py").write_text(test_source)
    harness.prepare(path)
    harness.approve()
    run = harness.execute()
    assert run["stage"] == "validating"
    assert run["attempts"][-1]["outcome"] == outcome
    assert run["corrections"] == 0
    with pytest.raises(HarnessError):
        harness.accept()


def test_missing_registered_command_stops_without_fix_retry(workspace):
    harness, plan, path, save = workspace
    plan["validation"].insert(0, {"argv": ["nonexistent-harness-command-12345.exe"], "kind": "command"})
    save()
    harness.prepare(path)
    harness.approve()
    run = harness.execute()
    assert run["stage"] == "validating"
    assert run["attempts"][-1]["outcome"] == "missing"
    assert run["corrections"] == 0


def test_timeout_is_interruption_with_log(workspace):
    harness, plan, path, save = workspace
    plan["validation"].insert(0, {"argv": ["{python}", "-c", "import time; time.sleep(30)"], "kind": "command", "timeout": 0.15})
    save()
    harness.prepare(path)
    harness.approve()
    run = harness.execute()
    attempt = run["attempts"][-1]
    assert attempt["outcome"] == "interrupted"
    assert run["corrections"] == 0
    assert not alive(attempt["process"])
    assert Path(attempt["log"]).exists()


def test_command_that_changes_project_invalidates_its_result(workspace):
    harness, plan, path, save = workspace
    plan["validation"].insert(0, {"argv": ["{python}", "-c", "from pathlib import Path; Path('value.py').write_text('edited during test')"], "kind": "command"})
    save()
    harness.prepare(path)
    harness.approve()
    with pytest.raises(HarnessError, match="Unexpected file"):
        harness.execute()
    assert harness.store.get()["attempts"][-1]["outcome"] == "unverified"
    assert (harness.project / "value.py").read_text() == "edited during test"


def test_two_contending_runners_only_one_owns_project(workspace, tmp_path):
    harness, plan, path, save = workspace
    marker = tmp_path / "validation_started"
    source = f"import time\nfrom pathlib import Path\ndef test_wait():\n    Path({str(marker)!r}).write_text('started')\n    time.sleep(2)\n"
    (harness.project / "test_value.py").write_text(source)
    save()
    harness.prepare(path)
    harness.approve()
    first = running_cli(harness, "run")
    try:
        until(marker.exists)
        second = cli(harness, "resume", expected=2)
        assert "Another process owns" in second["error"]
        output, error = first.communicate(timeout=20)
        assert first.returncode == 0, output + error
    finally:
        if first.poll() is None:
            first.kill()
            first.wait()


def test_force_killed_harness_stops_descendants_and_resumes(workspace, tmp_path):
    harness, _, path, _ = workspace
    marker = tmp_path / "once.json"
    source = (
        "import json, subprocess, sys, time\nfrom pathlib import Path\n"
        f"MARKER = Path({str(marker)!r})\n"
        "def test_interrupted_once():\n"
        "    if not MARKER.exists():\n"
        "        child = subprocess.Popen([sys.executable, '-c', 'import time; time.sleep(60)'])\n"
        "        MARKER.write_text(json.dumps({'pid': child.pid}))\n"
        "        time.sleep(60)\n"
        "    assert True\n"
    )
    (harness.project / "test_value.py").write_text(source)
    harness.prepare(path)
    harness.approve()
    process = running_cli(harness, "run")
    try:
        until(marker.exists)
        child_id = identity(json.loads(marker.read_text())["pid"])
        current = harness.store.get()
        worker_id = current["attempts"][-1]["process"]
        process.kill()
        process.communicate(timeout=10)
        until(lambda: not alive(worker_id) and not alive(child_id))
        before = harness.store.get()["attempts"][-1]
        assert before["outcome"] == "running"
        resumed = cli(harness, "resume")
        assert resumed["stage"] == "awaiting_acceptance"
        old = next(a for a in resumed["attempts"] if a["id"] == before["id"])
        assert old["outcome"] == "interrupted"
        assert old["duration"] is None
        assert len({a["id"] for a in resumed["attempts"]}) == len(resumed["attempts"])
    finally:
        if process.poll() is None:
            process.kill()
            process.wait()


def test_residual_recorded_process_blocks_resume(workspace):
    harness, _, path, _ = workspace
    harness.prepare(path)
    run = harness.approve()
    process = subprocess.Popen([sys.executable, "-c", "import time; time.sleep(30)"])
    try:
        run["attempts"].append({"id": "orphan", "outcome": "running", "process": identity(process.pid)})
        harness.store.save(run, "test_orphan")
        with pytest.raises(HarnessError, match="still active"):
            harness.execute()
    finally:
        process.kill()
        process.wait()


def test_pid_reuse_is_not_mistaken_for_original_worker():
    record = identity()
    assert alive(record)
    assert not alive({**record, "created": record["created"] - 10})


def test_alternate_state_directory_does_not_bypass_active_run(workspace, tmp_path):
    harness, _, path, _ = workspace
    harness.prepare(path)
    alternate = Harness(harness.project, tmp_path / "other-state")
    with pytest.raises(HarnessError, match="another state directory"):
        alternate.prepare(path)


def test_ownership_record_survives_exit_while_collecting_new_owner(workspace, tmp_path):
    harness, _, path, _ = workspace
    harness.prepare(path)
    source = (
        "import os, sys\n"
        "from development_harness.runner import Harness\n"
        "from development_harness import processes\n"
        "h = Harness(sys.argv[1], sys.argv[2])\n"
        "processes.identity = lambda: os._exit(99)\n"
        "h.approve()\n"
    )
    crashed = subprocess.run(
        [sys.executable, "-c", source, str(harness.project), str(harness.store.home)],
        capture_output=True, timeout=15, creationflags=subprocess.CREATE_NO_WINDOW,
    )
    assert crashed.returncode == 99, crashed.stdout + crashed.stderr
    alternate = Harness(harness.project, tmp_path / "other-state")
    with pytest.raises(HarnessError, match="another state directory"):
        alternate.prepare(path)
    assert alternate.store.active() is None
    assert cli(harness, "approve")["stage"] == "implementing"


@pytest.mark.parametrize("after_replace", [False, True])
@pytest.mark.parametrize("legacy", [False, True])
def test_ownership_survives_process_exit_at_atomic_replace(workspace, tmp_path, after_replace, legacy):
    from development_harness.processes import default_home

    harness, _, path, _ = workspace
    harness.prepare(path)
    directory = default_home() / "ownership"
    lock = directory / (harness.store.project_id + ".lock")
    record = directory / (harness.store.project_id + ".json")
    if legacy:
        lock.write_bytes(b"\0" + record.read_bytes())
        record.unlink()
    stable_lock = lock.read_bytes()
    source = (
        "import os, sys\n"
        "from development_harness.runner import Harness\n"
        "from development_harness import processes\n"
        "h = Harness(sys.argv[1], sys.argv[2])\n"
        "replace = processes.os.replace\n"
        "def interrupted_replace(source, target):\n"
        "    if sys.argv[3] == 'after':\n"
        "        replace(source, target)\n"
        "    os._exit(99)\n"
        "processes.os.replace = interrupted_replace\n"
        "h.approve()\n"
    )
    crashed = subprocess.run(
        [sys.executable, "-c", source, str(harness.project), str(harness.store.home),
         "after" if after_replace else "before"],
        capture_output=True, timeout=15, creationflags=subprocess.CREATE_NO_WINDOW,
    )
    assert crashed.returncode == 99, crashed.stdout + crashed.stderr
    assert lock.read_bytes() == stable_lock
    assert harness.store.get()["stage"] == "awaiting_approval"
    alternate = Harness(harness.project, tmp_path / "other-state")
    error = cli(alternate, "prepare", "--plan", str(path), expected=2)
    assert "another state directory" in error["error"]
    assert alternate.store.active() is None
    assert cli(harness, "approve")["stage"] == "implementing"


def test_missing_pytest_stops_without_corrections_and_resumes_after_environment_repair(workspace, tmp_path):
    harness, plan, path, save = workspace
    environment = tmp_path / "python without pytest"
    venv.EnvBuilder(with_pip=False).create(environment)
    plan["validation"][0]["argv"][0] = str(environment / "Scripts" / "python.exe")
    save()
    cli(harness, "prepare", "--plan", str(path))
    cli(harness, "approve")
    stopped = cli(harness, "run", expected=1)
    assert stopped["stage"] == "validating"
    assert stopped["corrections"] == 0
    assert len([a for a in stopped["attempts"] if a["role"] == "developer"]) == 1
    attempt = stopped["attempts"][-1]
    assert attempt["outcome"] == "unverified"
    assert attempt["exit_code"] == 1
    assert "environment" in stopped["reason"]
    assert "No module named pytest" in Path(attempt["log"]).read_text()
    assert "not complete" in cli(harness, "accept", expected=2)["error"]

    # Reuse the installed test dependencies without network access or changing the plan/project.
    (environment / "Lib" / "site-packages" / "test-dependencies.pth").write_text(
        sysconfig.get_path("purelib") + "\n", encoding="utf-8",
    )
    resumed = cli(harness, "resume")
    assert resumed["stage"] == "awaiting_acceptance"
    assert resumed["corrections"] == 0
    assert len([a for a in resumed["attempts"] if a["role"] == "developer"]) == 1
    assert resumed["approval"] == stopped["approval"]
    old = next(a for a in resumed["attempts"] if a["id"] == attempt["id"])
    assert old["outcome"] == "unverified"
