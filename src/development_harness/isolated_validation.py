"""Pinned Python/pytest checks on content-identical, read-only project copies."""

import copy
import hashlib
from importlib import metadata
import json
from pathlib import Path
import re
import shutil
import sys
import time
import uuid
import xml.etree.ElementTree as ET

from .appcontainer_probe import copy_runtime, diagnose_appcontainer, tree_hash
from .files import require_single_link, require_snapshot, snapshot, target
from .model import HarnessError, digest, validate_checks
from .project import SENSITIVE_PARTS
from .store import check_home
from .validation import pytest_result
from .windows_appcontainer import AppContainer
from .worker_contract import save_record


DISTRIBUTIONS = {"pytest": "9.1.1", "pluggy": "1.6.0", "iniconfig": "2.3.0", "packaging": "26.3",
                 "pygments": "2.21.0", "colorama": "0.4.6", "psutil": "7.2.2"}
ENTRY = Path(__file__).with_name("validation_entry.py")


def failure_classification(outcome, junit):
    """Separate verified code failures from faults that cannot justify a retry.

    Only structured JUnit exception fields are considered, never process output.
    An unknown exception or incomplete suite stops for inspection. This does not
    change the underlying result, including the legacy ``failed`` outcome.
    """
    if outcome == "passed":
        return None
    if outcome == "interrupted":
        return "interrupted"
    if outcome != "failed":
        return "validation_incomplete"
    try:
        cases = list(ET.parse(junit).getroot().iter("testcase"))
    except (OSError, ET.ParseError):
        return "validation_incomplete"
    if not cases or any(case.find("skipped") is not None for case in cases):
        return "validation_incomplete"
    kinds = []
    code_exceptions = {"AssertionError", "AttributeError", "IndexError", "KeyError", "NameError",
                       "NotImplementedError", "RecursionError", "RuntimeError", "StopIteration",
                       "SyntaxError", "TypeError", "UnboundLocalError", "ValueError", "ZeroDivisionError"}
    environment_exceptions = {"ImportError", "ModuleNotFoundError", "FileNotFoundError", "OSError",
                              "IOError", "ConnectionError", "TimeoutError", "MemoryError"}
    for case in cases:
        for problem in (child for child in case if child.tag in {"failure", "error"}):
            message = problem.get("message", "").strip()
            # Pytest fixture errors wrap the exception in this JUnit attribute.
            message = re.sub(r'^failed on (?:setup|teardown) with [\"\']', "", message)
            exception = problem.get("type", "").rsplit(".", 1)[-1]
            if not exception:
                match = re.match(r"([A-Za-z_][A-Za-z_0-9]*(?:Error|Exception))(?::|$)", message)
                exception = match.group(1) if match else ""
            if exception == "PermissionError" or re.match(r"\[(?:Errno 13|WinError 5)\]", message):
                kinds.append("permission")
            elif exception in environment_exceptions or problem.tag == "error":
                kinds.append("environment")
            elif exception in code_exceptions or (not exception and message.startswith("assert ")):
                kinds.append("code")
            else:
                kinds.append("validation_incomplete")
    for stop in ("permission", "environment", "validation_incomplete"):
        if stop in kinds:
            return stop
    return "code" if kinds else "validation_incomplete"


def copy_validation_runtime(directory):
    distributions = []
    for name, version in DISTRIBUTIONS.items():
        try:
            distribution = metadata.distribution(name)
        except metadata.PackageNotFoundError as exc:
            raise HarnessError("Required validation dependency is not installed: " + name) from exc
        if distribution.version != version or not distribution.files:
            raise HarnessError("Validation dependency differs from the reviewed lock: " + name + "==" + version)
        distributions.append(distribution)
    executable = copy_runtime(directory)
    site = directory / "Lib/site-packages"
    for distribution in distributions:
        for entry in distribution.files:
            parts = entry.parts
            if ".." in parts or "__pycache__" in parts or entry.suffix in {".pth", ".pyc"}:
                continue  # No console-script executables, startup hooks or editable installs.
            source = Path(distribution.locate_file(entry))
            if not source.is_file() or source.is_symlink() or source.is_junction():
                raise HarnessError("Pinned dependency contains a missing or linked file: " + str(entry))
            require_single_link(source, source.stat())
            output = site / str(entry)
            output.parent.mkdir(parents=True, exist_ok=True)
            shutil.copy2(source, output)
    (directory / "dependencies.json").write_text(json.dumps(DISTRIBUTIONS, indent=2), encoding="utf-8")
    return executable


def copied_path(name):
    parts = [p.casefold() for p in name.split("/")]
    return not (set(parts) & (SENSITIVE_PARTS | {"harness-project.json"}) or parts[:2] == ["phase", "generated"] or
                any(p.startswith(".env") for p in parts) or parts[-1].endswith((".env", ".pem", ".key", ".pfx", ".p12")))


def pytest_arguments(check):
    check = copy.deepcopy(check)
    validate_checks([check])
    if check["kind"] != "pytest" or not (check["argv"][:3] == ["{python}", "-m", "pytest"] or
            check["argv"][:3] == [sys.executable, "-m", "pytest"]):
        raise HarnessError("Isolated validation supports the reviewed harness Python -m pytest command only.")
    for value in check["argv"][3:]:
        if value == "-s" or value.startswith(("--basetemp", "--rootdir", "--confcutdir", "--capture", "--log-file")) or re.match(r"^[A-Za-z]:", value) or value.startswith(("/", "\\")):
            raise HarnessError("Isolated pytest paths and temporary directories must stay within its copied project.")
    return check


class IsolatedValidator:
    def __init__(self, directory):
        self.directory = Path(directory).resolve()
        self.directory.mkdir(parents=True, exist_ok=False)
        self.policy = None
        self.runtime = None

    def verify(self):
        self.policy = None
        report = diagnose_appcontainer(self.directory / ("p-" + uuid.uuid4().hex[:12]), runtime_factory=copy_validation_runtime)
        if not report["ready"]:
            raise HarnessError("Isolated validation permission/dependency verification failed: " + report["evidence_directory"])
        self.runtime = Path(report["evidence_directory"]) / "runtime"
        self.runtime_hashes = tree_hash(self.runtime)
        self.entry_hash = hashlib.sha256(ENTRY.read_bytes()).hexdigest()
        self.policy = report
        return report

    def run(self, check, project, *, launched=lambda _: None, attempt_id=None):
        check = pytest_arguments(check)
        project = Path(project).resolve(strict=True)
        check_home(self.directory, project)
        if self.policy is None or not self.policy["ready"]:
            raise HarnessError("Verify the AppContainer boundary before isolated validation.")
        if tree_hash(self.runtime) != self.runtime_hashes or hashlib.sha256(ENTRY.read_bytes()).hexdigest() != self.entry_hash:
            self.policy = None
            raise HarnessError("Verified validation runtime/bootstrap changed; reverify before execution.")
        baseline = snapshot(project)
        directory = self.directory / ("c-" + uuid.uuid4().hex[:12])
        work, scratch = directory / "project", directory / "tmp"
        work.mkdir(parents=True)
        scratch.mkdir()
        evidence = {"id": attempt_id or directory.name, "outcome": "preparing", "content_version": digest(baseline),
                    "source_project": str(project), "copied_project": str(work), "argv": check["argv"],
                    "check_hash": digest(check), "backend": "appcontainer", "started": time.time(),
                    "permission_report": str(Path(self.policy["evidence_directory"]) / "report.json"),
                    "dependencies": dict(DISTRIBUTIONS), "excluded_paths": [], "tests": 0,
                    "record": str(directory / "validation.json")}
        container = None
        try:
            for name, expected in baseline.items():
                if not copied_path(name):
                    evidence["excluded_paths"].append(name)
                    continue
                original = target(project, name)
                require_single_link(original, original.stat())
                content = original.read_bytes()
                if hashlib.sha256(content).hexdigest() != expected:
                    raise HarnessError("Project changed while preparing isolated validation: " + name)
                destination = work / name
                destination.parent.mkdir(parents=True, exist_ok=True)
                destination.write_bytes(content)
            require_snapshot(project, baseline)
            copied = tree_hash(work)
            save_record(directory / "source-manifest.json", {"original": baseline, "copy": copied})
            bootstrap = directory / "entry.py"
            shutil.copy2(ENTRY, bootstrap)
            junit = scratch / "junit.xml"
            specification = {"project": str(work), "scratch": str(scratch), "args": check["argv"][3:] + [
                "--capture=sys", "-p", "no:cacheprovider", "--rootdir", str(work), "--confcutdir", str(work),
                "--basetemp", str(scratch / "pytest"), "--log-file", str(scratch / "pytest.log"),
                "--junitxml", str(junit), "-o", "junit_family=xunit2"]}
            evidence["effective_pytest_args"] = specification["args"]
            save_record(directory / "invocation.json", specification)
            save_record(directory / "validation.json", evidence)
            container = AppContainer(self.directory)

            def dispatched(record):
                evidence.update(record)
                save_record(directory / "validation.json", evidence)
                launched(evidence)

            with container:
                for path in (self.runtime, work, bootstrap, directory / "invocation.json"):
                    container.grant(path)
                container.grant(scratch, write=True)
                result = container.run([self.runtime / "python.exe", "-I", "-B", "-X", "utf8", bootstrap, directory / "invocation.json"],
                                       work, directory / "process", timeout=check["timeout"], scratch=scratch, launched=dispatched)
            evidence.update(process_result=result, exit_code=result["exit_code"],
                            log=str(directory / "process/stdout.log"), stderr=str(directory / "process/stderr.log"))
            require_snapshot(project, baseline)
            if tree_hash(work) != copied or tree_hash(self.runtime) != self.runtime_hashes:
                self.policy = None
                raise HarnessError("Isolated project/runtime changed; validation evidence is invalid.")
            if junit.exists():
                require_single_link(junit, junit.stat())
                if junit.is_symlink() or junit.is_junction() or junit.stat().st_size > 5_000_000:
                    raise HarnessError("Unexpected pytest result artifact.")
                shutil.copyfile(junit, directory / "pytest.xml")
                evidence["junit"] = str(directory / "pytest.xml")
            if result["outcome"] == "interrupted":
                evidence.update(outcome="interrupted", reason="Validation deadline; process tree terminated.")
            elif result["exit_code"] == 5:
                evidence["outcome"] = "no_tests"
            else:
                outcome, count = pytest_result(directory / "pytest.xml")
                evidence["tests"] = count
                evidence["outcome"] = (outcome if result["exit_code"] == 0 else
                                       "failed" if result["exit_code"] == 1 and outcome == "failed" else "unverified")
        except KeyboardInterrupt:
            evidence.update(outcome="interrupted", reason="Validation interrupted; process tree terminated.")
            raise
        except Exception as exc:
            evidence.update(outcome="unverified", reason=str(exc))
            if isinstance(exc, PermissionError):
                evidence["failure_kind"] = "permission"
        finally:
            if container:
                evidence["container"] = container.record
            interrupted = evidence["outcome"] == "interrupted"
            evidence.update(ended=None if interrupted else time.time())
            evidence["duration"] = None if interrupted else evidence["ended"] - evidence["started"]
            evidence.setdefault("failure_kind", failure_classification(evidence["outcome"], directory / "pytest.xml"))
            evidence["stop_kind"] = evidence["failure_kind"] if evidence["failure_kind"] != "code" else None
            save_record(directory / "validation.json", evidence)
        return evidence


def review_evidence(result):
    """Bounded actual results from this invocation, without loading other logs."""
    return {key: result[key] for key in ("id", "content_version", "check_hash", "outcome", "tests", "argv")} | {
        "exit_code": result.get("exit_code"), "reason": result.get("reason"),
        "failure_kind": result.get("failure_kind"), "stop_kind": result.get("stop_kind"),
        "stdout": result.get("process_result", {}).get("stdout", "")[-16000:],
        "stderr": result.get("process_result", {}).get("stderr", "")[-8000:]}
