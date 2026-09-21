"""Disposable Windows command-boundary investigation for Phase 3 admission.

This is a synthetic probe, not a permission grant or a live AI worker adapter.
Only files created by this invocation and a controller-owned loopback listener
are touched. The current candidate is explicitly the unelevated Codex backend.
"""

import hashlib
import json
from pathlib import Path
import re
import socket
import socketserver
import subprocess
import sys
import threading
import time

from .codex_adapter import command_result, environment, executable
from .model import HarnessError
from .processes import Job


REVIEWED_PROBE_VERSIONS = {"codex-cli 0.155.1"}
ROLES = ("developer", "reviewer", "validation")
INITIAL = "synthetic original\n"
REQUIRED_OPTIONS = {"--permission-profile", "--cd", "--config", "--include-managed-config"}
PAYLOAD = Path(__file__).with_name("worker_probe_payload.py")


def _toml(value):
    if isinstance(value, dict):
        return "{" + ", ".join(json.dumps(k) + "=" + _toml(v) for k, v in value.items()) + "}"
    return json.dumps(value)


def permission_profile(project, role):
    """Candidate profile: explicit writable directories; all other paths read-only.

    Broad read access is a recorded limitation, not a claim of read isolation.
    No profile from the target project or the user's Codex config is loaded.
    """
    if role not in ROLES:
        raise HarnessError("Unknown worker probe role: " + str(role))
    project = Path(project).resolve()
    filesystem = {":root": "read", str(project): "read"}
    if role == "developer":
        filesystem[str(project / "src")] = "write"
    if role in {"developer", "validation"}:
        filesystem[str(project / "tmp")] = "write"
    return {"filesystem": filesystem, "network": {"enabled": False}}


def _run(argv, directory, env, timeout=25):
    job, worker = Job(), None
    started = time.time()
    try:
        worker = subprocess.Popen(argv, cwd=directory, env=env,
                                  stdin=subprocess.DEVNULL, stdout=subprocess.PIPE,
                                  stderr=subprocess.PIPE, creationflags=subprocess.CREATE_NO_WINDOW)
        job.assign(worker.pid)
        try:
            out, err = worker.communicate(timeout=timeout)
        except subprocess.TimeoutExpired:
            job.close()
            if worker.poll() is None:
                worker.kill()
            out, err = worker.communicate(timeout=5)
            return {"outcome": "interrupted", "exit_code": worker.returncode,
                    "stdout": out.decode("utf-8", errors="replace"),
                    "stderr": err.decode("utf-8", errors="replace"), "duration": None}
        return {"outcome": "finished", "exit_code": worker.returncode,
                "stdout": out.decode("utf-8", errors="replace"),
                "stderr": err.decode("utf-8", errors="replace"),
                "duration": time.time() - started}
    finally:
        job.close()
        if worker:
            if worker.poll() is None:
                worker.kill()
            worker.wait(timeout=5)


def evaluate_role(role, process, expected, originals, received):
    """Judge host-observed files and receipt evidence as well as process output."""
    checks = {}
    observations = None
    try:
        observations = json.loads(process["stdout"])
        parent, child = observations["parent"], observations["child"]
        if (process["outcome"] != "finished" or process["exit_code"] != 0 or
                observations["child_exit_code"] != 0 or parent["pid"] == child["pid"]):
            raise ValueError("Incomplete or non-distinct process evidence")
        for generation, record in (("parent", parent), ("child", child)):
            for name, allowed in expected.items():
                observed = record["writes"][name]
                checks[generation + ":" + name] = (
                    observed["outcome"] == ("written" if allowed else "denied")
                )
            label = role + ":" + generation
            checks[generation + ":network_denied"] = (
                record["network"]["outcome"] == "denied" and label not in received
            )
        checks["distinct_child_process"] = True
    except (KeyError, TypeError, ValueError):
        checks["valid_process_evidence"] = False
    for name, path in originals.items():
        try:
            content = Path(path).read_text(encoding="utf-8")
            wanted = role + ":child\n" if expected[name] else INITIAL
            checks["file:" + name] = content == wanted
        except (OSError, UnicodeError):
            checks["file:" + name] = False
    return {"role": role, "checks": checks, "passed": bool(checks) and all(checks.values()),
            "observations": observations}


def diagnose_workers(directory, *, codex_path=None):
    directory = Path(directory).resolve()
    directory.mkdir(parents=True, exist_ok=False)
    report = {"format": 1, "created": time.time(), "ready": False, "execution_enabled": False, "actual_ai_calls": 0,
              "backend": "unelevated", "profile": "disposable-worker-probe-v1",
              "scope": "Synthetic command and descendant probes; not live AI-role verification.",
              "evidence_directory": str(directory), "roles": [], "checks": {}, "next_steps": [],
              "limitations": ["The candidate allows broad filesystem reads.",
                              "Only an owned loopback TCP listener is probed; external services are not contacted.",
                              "Passing this investigation does not grant workflow execution or prove all P3-T2 conditions."]}
    try:
        exe = executable(codex_path)
        binary_hash = hashlib.sha256(exe.read_bytes()).hexdigest()
        report.update(executable=str(exe), binary_hash=binary_hash)
        report["probe_code_sha256"] = {p.name: hashlib.sha256(p.read_bytes()).hexdigest()
                                       for p in (Path(__file__), PAYLOAD)}
        result = command_result([str(exe), "--version"], directory)
        version = result.stdout.strip()
        report["version"] = version
        report["checks"]["reviewed_version"] = result.returncode == 0 and version in REVIEWED_PROBE_VERSIONS
        if not report["checks"]["reviewed_version"]:
            report["next_steps"].append("Review this CLI's worker-probe contract; Planner version support is unchanged.")
            return report
        help_result = command_result([str(exe), "sandbox", "--help"], directory)
        (directory / "sandbox-help.txt").write_text(help_result.stdout, encoding="utf-8")
        report["checks"]["sandbox_options"] = help_result.returncode == 0 and REQUIRED_OPTIONS <= set(
            re.findall(r"--[a-z][a-z-]*\b", help_result.stdout))
        if not report["checks"]["sandbox_options"]:
            report["next_steps"].append("The selected CLI lacks the reviewed sandbox profile command contract.")
            return report
        _probe_roles(directory, exe, report)
        report["checks"]["unchanged_executable"] = hashlib.sha256(exe.read_bytes()).hexdigest() == binary_hash
        report["ready"] = all(report["checks"].values()) and all(role["passed"] for role in report["roles"])
        if not report["ready"]:
            report["next_steps"].append(
                "Do not connect live workers using this candidate. Prepare a stronger permission backend "
                "and rerun command, descendant and live-role probes before P3-T2 admission.")
    except (HarnessError, OSError, UnicodeError) as exc:
        report["error"] = str(exc)
        report["checks"]["probe_completed"] = False
        report["next_steps"].append("Inspect the saved evidence; a failed or incomplete probe cannot authorize execution.")
    finally:
        (directory / "report.json").write_text(json.dumps(report, ensure_ascii=False, indent=2) + "\n", encoding="utf-8")
    return report


def _probe_roles(directory, exe, report):
    received = []

    class Handler(socketserver.BaseRequestHandler):
        def handle(self):
            self.request.settimeout(3)
            try:
                label = self.request.recv(128).decode("ascii")
                received.append(label)
                self.request.sendall(b"ack")
            except (OSError, UnicodeError):
                pass

    server = socketserver.ThreadingTCPServer(("127.0.0.1", 0), Handler)
    server.daemon_threads = True
    thread = threading.Thread(target=server.serve_forever, kwargs={"poll_interval": 0.05}, daemon=True)
    thread.start()
    processes = []
    try:
        port = server.server_address[1]

        def positive_control(label):
            try:
                with socket.create_connection(("127.0.0.1", port), timeout=3) as connection:
                    connection.sendall(label.encode("ascii"))
                    return connection.recv(16) == b"ack"
            except OSError:
                return False

        report["checks"]["network_control_before"] = positive_control("host:before")
        if not report["checks"]["network_control_before"]:
            return
        for role in ROLES:
            root = directory / role
            project, controller, home = root / "work", root / "control", root / "home"
            home.mkdir(parents=True)
            paths = {
                "project": project / "src" / "value.py",
                "scratch": project / "tmp" / "scratch.txt",
                "git": project / ".git" / "config",
                "project_policy": project / "harness-project.json",
                "plan": project / "Phase" / "Generated" / "plan.json",
                "runner": controller / "runner.py",
                "approval": controller / "state.sqlite3",
                "installed_package": controller / "site-packages" / "package.py",
                "unrelated": root / "other" / "file.txt",
            }
            for path in paths.values():
                path.parent.mkdir(parents=True, exist_ok=True)
                path.write_text(INITIAL, encoding="utf-8")
            expected = {name: name == "project" and role == "developer" or
                        name == "scratch" and role in {"developer", "validation"} for name in paths}
            specification = {"role": role, "port": port, "paths": {k: str(v) for k, v in paths.items()}}
            spec = project / "probe-input.json"
            spec.write_text(json.dumps(specification), encoding="utf-8")
            profile = permission_profile(project, role)
            (root / "profile.json").write_text(json.dumps(profile, indent=2), encoding="utf-8")
            argv = [str(exe), "sandbox", "-P", "harness_probe", "--include-managed-config", "-C", str(project),
                    "-c", "permissions=" + _toml({"harness_probe": profile}),
                    "-c", 'windows.sandbox="unelevated"', "-c", 'approval_policy="never"',
                    "--", Path(sys.executable).as_posix(), "-I", "-B", PAYLOAD.as_posix(), spec.name]
            env = environment()
            env["CODEX_HOME"] = str(home)
            (root / "command.json").write_text(json.dumps(argv, indent=2), encoding="utf-8")
            process = _run(argv, project, env)
            (root / "process.json").write_text(json.dumps(process, indent=2), encoding="utf-8")
            processes.append((role, process, expected, paths))
        report["checks"]["network_control_after"] = positive_control("host:after")
    finally:
        server.shutdown()
        server.server_close()
        thread.join(timeout=3)
    report["network_receipts"] = received
    report["checks"]["all_roles_executed"] = len(processes) == len(ROLES)
    for role, process, expected, paths in processes:
        report["roles"].append(evaluate_role(role, process, expected, paths, received))
