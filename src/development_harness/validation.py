"""Run approved commands and classify real outcomes, including empty pytest suites."""

import json
import os
from pathlib import Path
import subprocess
import sys
import time
import xml.etree.ElementTree as ET

from .processes import Job, identity


def pytest_result(path):
    try:
        cases = list(ET.parse(path).getroot().iter("testcase"))
    except (OSError, ET.ParseError):
        return "unverified", 0
    executed = [case for case in cases if case.find("skipped") is None]
    if not executed:
        return "no_tests", 0
    if any(case.find("failure") is not None or case.find("error") is not None for case in executed):
        return "failed", len(executed)
    if len(executed) != len(cases):
        return "unverified", len(executed)
    return "passed", len(executed)


def validate(check, project, directory, attempt, launched):
    directory = Path(directory)
    log = directory / (attempt["id"] + ".log")
    result_path = directory / (attempt["id"] + ".result.json")
    junit = directory / (attempt["id"] + ".xml")
    argv = [sys.executable if value == "{python}" else value for value in check["argv"]]
    if check["kind"] == "pytest":
        argv += ["--junitxml", str(junit), "-o", "junit_family=xunit2"]
    attempt.update(argv=argv, log=str(log), started=time.time(), outcome="launching")
    env = os.environ.copy()
    env.update(PYTHONDONTWRITEBYTECODE="1", PYTEST_ADDOPTS="", PYTEST_DISABLE_PLUGIN_AUTOLOAD="1")
    job = Job()
    worker = None
    try:
        with log.open("wb") as output:
            worker = subprocess.Popen(
                [sys.executable, str(Path(__file__).with_name("gate.py")), str(result_path)],
                cwd=project, stdin=subprocess.PIPE, stdout=output, stderr=subprocess.STDOUT,
                env=env, creationflags=subprocess.CREATE_NO_WINDOW,
            )
            job.assign(worker.pid)
            attempt.update(process=identity(worker.pid), outcome="running")
            launched(attempt)  # Persist PID identity BEFORE allowing any project command.
            worker.stdin.write(json.dumps({"argv": argv}).encode() + b"\n")
            worker.stdin.flush()
            worker.stdin.close()
            try:
                worker.wait(timeout=check["timeout"])
            except subprocess.TimeoutExpired:
                attempt["outcome"] = "interrupted"
                attempt["reason"] = "Validation timeout; worker tree terminated. Resume to rerun."
            else:
                try:
                    result = json.loads(result_path.read_text(encoding="utf-8"))
                except (OSError, ValueError):
                    result = {"error": "Worker ended without confirmed command result."}
                attempt["exit_code"] = result.get("exit_code")
                if "error" in result:
                    attempt.update(outcome="missing", reason=result["error"])
                elif check["kind"] == "pytest" and result["exit_code"] == 5:
                    attempt.update(outcome="no_tests", tests=0)
                elif result["exit_code"] != 0:
                    if check["kind"] == "command":
                        attempt["outcome"] = "failed"
                    else:
                        outcome, tests = pytest_result(junit)
                        # Python also exits with 1 when pytest is unavailable. Only
                        # confirmed test failures authorize implementation retries.
                        if result["exit_code"] == 1 and outcome == "failed":
                            attempt.update(outcome="failed", tests=tests)
                        else:
                            attempt.update(outcome="unverified", reason=(
                                "pytest ended without confirmed test-failure evidence; "
                                "check the registered Python/pytest environment and command log before resuming."
                            ))
                elif check["kind"] == "pytest":
                    attempt["outcome"], attempt["tests"] = pytest_result(junit)
                else:
                    attempt["outcome"] = "passed"
    finally:
        job.close()
        if worker:
            if worker.stdin and not worker.stdin.closed:
                worker.stdin.close()
            if worker.poll() is None:
                worker.kill()
            worker.wait(timeout=10)
    attempt["ended"] = time.time()
    attempt["duration"] = attempt["ended"] - attempt["started"]
    return attempt
