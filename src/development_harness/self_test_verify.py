"""Isolated B unit checks and separately authorized, reviewed host regression.

The host subcommand is intentionally absent from Workflow execution. Its input
hash is the operator's explicit declaration that these exact tests were reviewed.
Evidence hashes detect accidental changes, not a malicious host user/test.
"""

import argparse
import json
import os
from pathlib import Path
import shutil
import subprocess
import sys
import time

from .files import snapshot, require_snapshot
from .frozen_entry import file_hash, guard_paths, inspect_runner, current_artifact_id, plain_path
from .isolated_validation import DISTRIBUTIONS, IsolatedValidator
from .model import HarnessError
from .processes import Job, identity
from .test_collection import complete_collection
from .validation import pytest_result
from .validation_profiles import SELF_TEST_PROFILE, prepare_profile
from .worker_contract import save_record


def current_profile(repository):
    return prepare_profile(Path(repository), snapshot(Path(repository)))


def artifact_files(paths):
    return {str(Path(path).resolve()): file_hash(path) for path in paths}


def isolated(repository, directory, runner, timeout):
    validator = IsolatedValidator(directory / "validation")
    validator.verify()
    result = validator.run({"kind": "pytest", "argv": ["{python}", "-m", "pytest", "-q"],
                            "profile": SELF_TEST_PROFILE, "timeout": timeout}, repository)
    profile = result.get("validation_profile", current_profile(repository))
    passed = result["outcome"] == "passed" and profile.get("isolated_complete") is True
    record = {"kind": "isolated", "runner_artifact": runner, "profile": profile,
              "passed": passed, "all_tests_complete": False, "tests": result["tests"],
              "validation": result, "artifacts": artifact_files([result["record"],
                  *([result["junit"], result["collection"]] if passed else [])])}
    save_record(directory / "report.json", record)
    return record


def reviewed_host(repository, directory, runner_root, runner, python, reviewed_version, timeout):
    baseline = snapshot(repository)
    profile = prepare_profile(repository, baseline)
    if reviewed_version != profile["input_version"]:
        raise HarnessError("Reviewed input version does not match current B; review the changed source/tests first.")
    python = plain_path(python).resolve(strict=True)
    if python.is_relative_to(repository) or python.is_relative_to(directory):
        raise HarnessError("Use a reviewed development Python outside B and its evidence directory.")
    project, scratch = directory / "project", directory / "tmp"
    scratch.mkdir()
    for name in baseline:
        if name in profile["inputs"]:
            target = project / name
            target.parent.mkdir(parents=True, exist_ok=True)
            shutil.copyfile(repository / name, target)
    require_snapshot(repository, baseline)
    copied = snapshot(project)
    if copied != profile["inputs"]:
        raise HarnessError("Copied host-test files do not match the reviewed input manifest.")
    entry, observer = directory / "entry.py", directory / "observer.py"
    shutil.copyfile(Path(__file__).with_name("reviewed_test_entry.py"), entry)
    shutil.copyfile(Path(__file__).with_name("test_collection.py"), observer)
    junit, collection = directory / "pytest.xml", directory / "collection.json"
    modules = sorted(profile["isolated_modules"] + [item["path"] for item in profile["host_modules"]])
    config = {"project": str(project), "observer": str(observer), "collection": str(collection),
              "environment": str(directory / "environment.json"),
              "dependencies": DISTRIBUTIONS | {"setuptools": "84.0.0"},
              "args": ["-q", *modules, "-p", "no:cacheprovider", "--rootdir", str(project),
                       "--confcutdir", str(project), "--basetemp", str(scratch / "p"),
                       "--junitxml", str(junit), "-o", "junit_family=xunit2"]}
    save_record(directory / "invocation.json", config)
    env = os.environ.copy()
    for key in ("PYTHONHOME", "PYTHONUSERBASE", "PYTHONSTARTUP", "PYTEST_PLUGINS",
                "DEVELOPMENT_HARNESS_TEST_SCRATCH"):
        env.pop(key, None)
    state = directory / "u"
    state.mkdir()
    env.update(PYTHONPATH=str(project / "src"), PYTHONDONTWRITEBYTECODE="1", PYTHONUTF8="1",
               PYTEST_DISABLE_PLUGIN_AUTOLOAD="1", PYTEST_ADDOPTS="", TEMP=str(scratch), TMP=str(scratch),
               LOCALAPPDATA=str(state), APPDATA=str(state),
               DEVELOPMENT_HARNESS_CODEX_PATH=str(runner_root / "tools/codex.exe"))
    record = {"kind": "reviewed-host", "runner_artifact": runner, "profile": profile, "passed": False,
              "reviewed_input_version": reviewed_version, "all_tests_complete": False, "started": time.time(),
              "warning": "Reviewed host tests have the operator's host permissions; this is not AppContainer execution."}
    job, process = Job(), None
    try:
        with (directory / "stdout.log").open("wb") as output:
            process = subprocess.Popen([str(python), "-I", "-B", "-X", "utf8", str(entry)],
                stdin=subprocess.PIPE, stdout=output, stderr=subprocess.STDOUT, cwd=directory,
                env=env, creationflags=subprocess.CREATE_NO_WINDOW)
            job.assign(process.pid)
            record["process"] = identity(process.pid)
            save_record(directory / "report.json", record)
            process.stdin.write(json.dumps(config).encode() + b"\n")
            process.stdin.close()
            try:
                record["exit_code"] = process.wait(timeout=timeout)
            except subprocess.TimeoutExpired:
                record["reason"] = "Reviewed host regression timed out; process tree terminated."
    finally:
        job.close()
        if process:
            if process.stdin and not process.stdin.closed:
                process.stdin.close()
            if process.poll() is None:
                process.kill()
            process.wait(timeout=10)
        record["duration"] = time.time() - record["started"]
        save_record(directory / "report.json", record)
    require_snapshot(repository, baseline)
    require_snapshot(project, copied)
    outcome, count = pytest_result(junit)
    observed = json.loads(collection.read_text(encoding="utf-8")) if collection.exists() else {}
    record.update(outcome=outcome, tests=count,
                  passed=record.get("exit_code") == 0 and outcome == "passed" and complete_collection(observed, modules, count),
                  artifacts=artifact_files([directory / name for name in
                      ("invocation.json", "environment.json", "stdout.log", "pytest.xml", "collection.json")
                      if (directory / name).exists()]))
    save_record(directory / "report.json", record)
    return record


def combine(repository, runner, isolated_report, host_report):
    profile = current_profile(repository)
    reports = []
    for path, kind in ((isolated_report, "isolated"), (host_report, "reviewed-host")):
        record = json.loads(Path(path).read_text(encoding="utf-8"))
        if (not isinstance(record, dict) or not isinstance(record.get("profile"), dict)
                or not isinstance(record.get("artifacts"), dict)):
            raise HarnessError("Malformed self-test report: " + str(path))
        if (record.get("kind") != kind or record.get("runner_artifact") != runner
                or record.get("profile", {}).get("inputs") != profile["inputs"]
                or record.get("profile", {}).get("input_version") != profile["input_version"]
                or record.get("passed") is not True or not record.get("artifacts")):
            raise HarnessError("Incomplete, stale or mismatched self-test report: " + str(path))
        for artifact, expected in record["artifacts"].items():
            if file_hash(artifact) != expected:
                raise HarnessError("Self-test evidence changed: " + artifact)
        if kind == "isolated":
            validation = record["validation"]
            junit, collected = Path(validation["junit"]), Path(validation["collection"])
            modules = profile["isolated_modules"]
        else:
            if record.get("reviewed_input_version") != profile["input_version"]:
                raise HarnessError("Host review does not cover these inputs.")
            junit, collected = Path(path).parent / "pytest.xml", Path(path).parent / "collection.json"
            modules = profile["isolated_modules"] + [item["path"] for item in profile["host_modules"]]
        outcome, count = pytest_result(junit)
        if (str(junit.resolve()) not in record["artifacts"] or str(collected.resolve()) not in record["artifacts"]
                or outcome != "passed" or count != record["tests"]
                or not complete_collection(json.loads(collected.read_text(encoding="utf-8")), modules, count)):
            raise HarnessError("Self-test module/execution coverage is incomplete: " + str(path))
        reports.append({"kind": kind, "tests": count, "report": str(Path(path).resolve()), "sha256": file_hash(path)})
    return {"profile": SELF_TEST_PROFILE, "runner_artifact": runner, "input_version": profile["input_version"],
            "all_tests_complete": True, "phase_accepted": False, "reports": reports,
            "scope": "Isolated unit suite plus explicitly reviewed full host regression on identical B inputs."}


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("mode", choices=("isolated", "reviewed-host", "report"))
    parser.add_argument("--repository", required=True)
    parser.add_argument("--runner", required=True)
    parser.add_argument("--directory", required=True, help="Fresh evidence directory outside A and B")
    parser.add_argument("--python", help="Reviewed development Python with requirements-dev.lock installed")
    parser.add_argument("--reviewed-input-version", help="Explicit host-test authorization for the reviewed source/test hash")
    parser.add_argument("--isolated-report")
    parser.add_argument("--host-report")
    parser.add_argument("--timeout", type=int, default=3600)
    args = parser.parse_args()
    try:
        root, repository, directory = (plain_path(value).resolve() for value in (args.runner, args.repository, args.directory))
        guard_paths(root, repository, directory)
        manifest = inspect_runner(root)
        runner = manifest["artifact_id"]
        if current_artifact_id() != runner or not sys.flags.isolated or not sys.dont_write_bytecode:
            raise HarnessError("Run this command from the selected frozen A runtime with -I -B.")
        if not 1 <= args.timeout <= 3600:
            raise HarnessError("Timeout must be between 1 and 3600 seconds.")
        if args.mode == "reviewed-host" and not (args.python and args.reviewed_input_version):
            raise HarnessError("Host tests require --python and --reviewed-input-version after reviewing B source/tests.")
        if args.mode == "report" and not (args.isolated_report and args.host_report):
            raise HarnessError("Both --isolated-report and --host-report are required.")
        directory.mkdir(parents=True, exist_ok=False)
        if args.mode == "isolated":
            record = isolated(repository, directory, runner, args.timeout)
        elif args.mode == "reviewed-host":
            record = reviewed_host(repository, directory, root, runner, args.python, args.reviewed_input_version, args.timeout)
        else:
            record = combine(repository, runner, args.isolated_report, args.host_report)
        if inspect_runner(root) != manifest:
            raise HarnessError("Runner A changed during verification; results are invalid.")
        save_record(directory / "report.json", record)
        version = record["input_version"] if args.mode == "report" else record["profile"]["input_version"]
        print(json.dumps({"report": str(directory / "report.json"), "passed": record.get("passed"),
                          "all_tests_complete": record["all_tests_complete"],
                          "input_version": version}, indent=2))
        return 0 if record.get("passed") or record["all_tests_complete"] else 1
    except (HarnessError, OSError, ValueError, KeyError, TypeError) as exc:
        print(json.dumps({"error": str(exc)}), file=sys.stderr)
        return 2


if __name__ == "__main__":
    raise SystemExit(main())
