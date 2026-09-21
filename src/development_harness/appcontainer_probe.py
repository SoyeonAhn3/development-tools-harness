"""Administrator-free candidate investigation; never grants live execution."""

from contextlib import ExitStack
import ctypes
import hashlib
import json
import os
from pathlib import Path
import platform
import shutil
import socket
import socketserver
import subprocess
import sys
import threading
import time

from .model import HarnessError
from .windows_appcontainer import ProbeContainer
from .worker_probe import INITIAL, ROLES, evaluate_role


PAYLOAD = Path(__file__).with_name("appcontainer_probe_payload.py")
NETWORKS = ("tcp4", "tcp6", "udp4", "udp6")
TOKEN = {"appcontainer": True, "capability_count": 0, "elevated": False}


def tree_hash(directory):
    return {str(path.relative_to(directory)): hashlib.sha256(path.read_bytes()).hexdigest()
            for path in sorted(directory.rglob("*")) if path.is_file()}


def copy_runtime(directory):
    """Copy the installed Python runtime only; never change installed file ACLs."""
    base = Path(sys.base_prefix)
    directory.mkdir(exist_ok=False)
    for path in base.iterdir():
        if path.is_file() and path.suffix.lower() in {".exe", ".dll"}:
            shutil.copy2(path, directory / path.name)
    shutil.copytree(base / "DLLs", directory / "DLLs")
    shutil.copytree(base / "Lib", directory / "Lib", ignore=shutil.ignore_patterns(
        "site-packages", "__pycache__", "test", "tests", "idlelib", "tkinter", "ensurepip"))
    return directory / "python.exe"


class Listeners:
    def __init__(self):
        self.received, self.endpoints = [], {}
        self.stack = ExitStack()

    def __enter__(self):
        received = self.received

        class TCP(socketserver.BaseRequestHandler):
            def handle(self):
                self.request.settimeout(2)
                try:
                    received.append(self.request.recv(128).decode("ascii"))
                    self.request.sendall(b"ack")
                except (OSError, UnicodeError):
                    pass

        class UDP(socketserver.BaseRequestHandler):
            def handle(self):
                data, connection = self.request
                try:
                    received.append(data.decode("ascii"))
                    connection.sendto(b"ack", self.client_address)
                except (OSError, UnicodeError):
                    pass

        try:
            for name in NETWORKS:
                ipv6, udp = name.endswith("6"), name.startswith("udp")
                base = socketserver.ThreadingUDPServer if udp else socketserver.ThreadingTCPServer
                server_type = type("OwnedListener", (base,), {"address_family": socket.AF_INET6 if ipv6 else socket.AF_INET,
                                                             "daemon_threads": True})
                server = server_type(("::1" if ipv6 else "127.0.0.1", 0), UDP if udp else TCP)
                self.stack.callback(server.server_close)
                thread = threading.Thread(target=server.serve_forever, kwargs={"poll_interval": 0.05}, daemon=True)
                thread.start()
                self.stack.callback(server.shutdown)
                self.endpoints[name] = list(server.server_address[:2])
        except BaseException:
            self.stack.close()
            raise
        return self

    def controls(self, label):
        result = {}
        for name, endpoint in self.endpoints.items():
            try:
                with socket.socket(socket.AF_INET6 if name.endswith("6") else socket.AF_INET,
                                   socket.SOCK_DGRAM if name.startswith("udp") else socket.SOCK_STREAM) as connection:
                    connection.settimeout(2)
                    connection.connect(tuple(endpoint))
                    connection.send((label + ":" + name).encode("ascii"))
                    result[label + ":" + name] = connection.recv(16) == b"ack"
            except OSError:
                result[label + ":" + name] = False
        return result

    def __exit__(self, *_):
        self.stack.close()


def evaluate(role, process, expected, paths, received):
    result = evaluate_role(role, process, expected, paths, received)
    checks = result["checks"]
    checks["host_verified_token"] = process.get("token") == TOKEN
    try:
        for generation in ("parent", "child"):
            record = result["observations"][generation]
            checks[generation + ":token"] = record["token"] == TOKEN
            for name in NETWORKS:
                checks[generation + ":" + name + "_denied"] = (
                    record["networks"][name]["outcome"] == "denied" and
                    role + ":" + generation + ":" + name not in received)
            for name in paths:
                checks[generation + ":read:" + name] = record["reads"][name] == (
                    "denied" if name in {"runner", "approval", "installed_package", "unrelated"} else "read")
    except (KeyError, TypeError):
        checks["complete_appcontainer_evidence"] = False
    result["passed"] = bool(checks) and all(checks.values())
    return result


def _roles(directory, runtime, executable, report):
    with Listeners() as listeners:
        report["checks"].update(listeners.controls("host:before"))
        if not all(report["checks"].values()):
            return
        for role in ROLES:
            root = directory / role
            project = root / "work"
            paths = {"project": project / "src/value.py", "scratch": project / "tmp/scratch.txt",
                     "git": project / ".git/config", "project_policy": project / "harness-project.json",
                     "plan": project / "Phase/Generated/plan.json", "runner": root / "control/runner.py",
                     "approval": root / "control/state.sqlite3", "installed_package": root / "control/site-packages/package.py",
                     "unrelated": root / "other/file.txt", "runtime": runtime / "probe-marker.txt"}
            for path in paths.values():
                path.parent.mkdir(parents=True, exist_ok=True)
                path.write_text(INITIAL, encoding="utf-8")
            expected = {name: (name == "project" and role == "developer" or
                               name == "scratch" and role in {"developer", "validation"}) for name in paths}
            payload = project / "payload.py"
            shutil.copy2(PAYLOAD, payload)
            input_path = project / "input.json"
            input_path.write_text(json.dumps({"role": role, "paths": {k: str(v) for k, v in paths.items()},
                                              "endpoints": listeners.endpoints}), encoding="utf-8")
            inputs = {path: hashlib.sha256(path.read_bytes()).hexdigest() for path in (payload, input_path)}
            container = ProbeContainer(directory)
            try:
                with container:
                    container.grant(runtime)
                    container.grant(project)
                    if role == "developer":
                        container.grant(project / "src", write=True)
                    if role in {"developer", "validation"}:
                        container.grant(project / "tmp", write=True)
                    process = container.run([executable, "-I", "-B", payload, input_path], project, root / "process")
            finally:
                (root / "profile.json").write_text(json.dumps(container.record, indent=2), encoding="utf-8")
            (root / "process.json").write_text(json.dumps(process, indent=2), encoding="utf-8")
            result = evaluate(role, process, expected, paths, listeners.received)
            result["checks"]["unchanged_probe_inputs"] = all(hashlib.sha256(p.read_bytes()).hexdigest() == h for p, h in inputs.items())
            result["checks"]["profile_removed"] = container.record.get("delete_hresult") == 0
            result["passed"] = all(result["checks"].values())
            report["roles"].append(result)
        report["checks"].update(listeners.controls("host:after"))
        report["network_receipts"] = list(listeners.received)
        report["checks"]["no_worker_network_receipts"] = all(
            receipt.startswith("host:") for receipt in listeners.received)


def diagnose_appcontainer(directory, *, runtime_factory=None):
    directory = Path(directory).resolve()
    directory.mkdir(parents=True, exist_ok=False)
    report = {"format": 1, "created": time.time(), "backend": "appcontainer", "ready": False,
              "execution_enabled": False, "actual_ai_calls": 0, "evidence_directory": str(directory),
              "profile": "disposable-appcontainer-probe-v1", "checks": {}, "roles": [], "next_steps": [],
              "scope": "Synthetic local permission evidence, not live AI-role or workflow admission.",
              "limitations": ["TCP/UDP IPv4/IPv6 probes contact owned loopback listeners only.",
                              "AppContainer has its own temporary profile and Windows-provided system reads.",
                              "Live adapters, approved patch application, isolated pytest, recovery and fixed-runner verification remain pending."]}
    try:
        if os.name != "nt":
            raise HarnessError("AppContainer investigation requires Windows.")
        report["windows"] = platform.version()
        report["checks"]["standard_user"] = not bool(ctypes.windll.shell32.IsUserAnAdmin())
        if not report["checks"]["standard_user"]:
            raise HarnessError("Run this administrator-free investigation from a standard-user process.")
        sources = (Path(__file__), PAYLOAD, Path(__file__).with_name("windows_appcontainer.py"))
        report["probe_code_sha256"] = {p.name: hashlib.sha256(p.read_bytes()).hexdigest() for p in sources}
        runtime = directory / "runtime"
        executable = (runtime_factory or copy_runtime)(runtime)
        before = tree_hash(runtime)
        (directory / "runtime-manifest.json").write_text(json.dumps(before, indent=2), encoding="utf-8")
        _roles(directory, runtime, executable, report)
        after = tree_hash(runtime)
        after.pop("probe-marker.txt", None)
        report["checks"]["unchanged_runtime"] = before == after
        report["ready"] = (len(report["roles"]) == len(ROLES) and all(report["checks"].values()) and
                           all(role["passed"] for role in report["roles"]))
    except (HarnessError, OSError, UnicodeError, ValueError, subprocess.SubprocessError) as exc:
        report["error"] = str(exc)
        report["checks"]["probe_completed"] = False
    finally:
        report["next_steps"].append(
            "Integrate and verify text-only Developer/Reviewer, controller-validated edits and AppContainer validation before live admission."
            if report["ready"] else "Inspect the failed evidence. Do not fall back to unrestricted execution or administrator setup.")
        (directory / "report.json").write_text(json.dumps(report, ensure_ascii=False, indent=2) + "\n", encoding="utf-8")
    return report
