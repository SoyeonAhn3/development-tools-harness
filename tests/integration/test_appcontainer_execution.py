import json
from pathlib import Path
import subprocess
import sys
import time
import uuid

import psutil
import pytest

from development_harness.appcontainer_probe import TOKEN
from development_harness.store import default_home
from development_harness.windows_appcontainer import ProbeContainer


@pytest.fixture(scope="module")
def actual_probe():
    root = default_home().parent / "test-appcontainer-probes" / uuid.uuid4().hex
    project = root / "project"
    project.mkdir(parents=True)
    (project / "value.py").write_text("original\n", encoding="utf-8")
    process = subprocess.run([sys.executable, "-m", "development_harness", "--project", str(project),
                              "--state-dir", str(root / "state"), "workflow-doctor"],
                             capture_output=True, text=True, encoding="utf-8", timeout=90)
    assert process.returncode == 0, process.stdout + process.stderr
    report = json.loads(process.stdout)
    assert (project / "value.py").read_text() == "original\n"
    assert set(path.name for path in project.iterdir()) == {"value.py"}
    return report


def test_actual_standard_user_roles_files_tokens_and_four_network_transports(actual_probe):
    report = actual_probe
    assert report["backend"] == "appcontainer"
    assert report["ready"]
    assert all(report["checks"].values())
    assert report["checks"]["standard_user"]
    assert len(report["roles"]) == 3
    assert len(report["network_receipts"]) == 8  # Host controls before/after on four transports.
    assert all(receipt.startswith("host:") for receipt in report["network_receipts"])
    for role in report["roles"]:
        assert role["passed"], role
        assert all(role["checks"].values())
        for generation in ("parent", "child"):
            record = role["observations"][generation]
            assert record["token"] == TOKEN
            assert all(value["outcome"] == "denied" for value in record["networks"].values())
    assert not report["execution_enabled"]
    assert report["actual_ai_calls"] == 0
    path = Path(report["evidence_directory"], "report.json")
    assert json.loads(path.read_text(encoding="utf-8")) == report


def test_actual_timeout_stops_appcontainer_and_descendant(actual_probe):
    root = Path(actual_probe["evidence_directory"])
    work = root / "timeout" / "work"
    scratch = work / "tmp"
    scratch.mkdir(parents=True)
    script = work / "wait.py"
    script.write_text("""import os,subprocess,sys,time
from pathlib import Path
if '--child' in sys.argv:
    Path('tmp/child.pid').write_text(str(os.getpid()))
    time.sleep(60)
else:
    subprocess.Popen([sys.executable,'-I','-B',__file__,'--child'],creationflags=subprocess.CREATE_NO_WINDOW)
    time.sleep(60)
""", encoding="utf-8")
    container = ProbeContainer(root)
    with container:
        container.grant(root / "runtime")
        container.grant(work)
        container.grant(scratch, write=True)
        result = container.run([root / "runtime/python.exe", "-I", "-B", script], work, root / "timeout/process", timeout=3)
    assert result["outcome"] == "interrupted"
    assert result["duration"] is None
    assert container.record["delete_hresult"] == 0
    child = int((scratch / "child.pid").read_text())
    assert child != result["pid"]
    for _ in range(30):
        if not any(psutil.pid_exists(pid) for pid in (child, result["pid"])):
            break
        time.sleep(0.1)
    assert not psutil.pid_exists(child)
    assert not psutil.pid_exists(result["pid"])


def test_appcontainer_does_not_silently_ignore_codex_selector(tmp_path):
    process = subprocess.run([sys.executable, "-m", "development_harness", "--project", str(tmp_path),
                              "workflow-doctor", "--codex-path", str(tmp_path / "unused.exe")],
                             capture_output=True, text=True, timeout=10)
    assert process.returncode == 2
    assert "--backend codex-unelevated" in process.stderr
    assert not list(tmp_path.iterdir())
