"""Explicit validation inputs for the harness's own isolated unit suite.

The profile names a partial check. Installation, CLI and OS-boundary regressions
require a separately reviewed host run and a mandatory manual acceptance check.
Project writing resources are test data; they never replace controller rules.
"""

from pathlib import PurePosixPath
import tomllib

from .model import HarnessError, digest
from .project import SENSITIVE_PARTS


SELF_TEST_PROFILE = "harness-self-v1"
HOST_CHECK_ID = "HARNESS_HOST_REGRESSION"
RESOURCE_FILES = (
    ".agents/skills/phase-doc/SKILL.md",
    ".agents/skills/phase-doc/references/phase-template.md",
)
HOST_UNIT_MODULES = {
    "test_appcontainer_temp.py": "Native junction creation and host startup assumptions",
    "test_frozen_integrity.py": "Checks installation ancestors outside the AppContainer grant",
    "test_self_test_verify.py": "Verifies host evidence paths and runner installation ancestors",
}


def validate_profile_command(check):
    if "profile" not in check:
        return
    if check["profile"] != SELF_TEST_PROFILE or check.get("kind") != "pytest":
        raise HarnessError("Unsupported validation profile; use harness-self-v1 with pytest.")
    if check["argv"][3:] not in ([], ["-q"]):
        raise HarnessError("The harness self-test profile selects its complete isolated suite; pytest filters are not allowed.")


def input_files(baseline):
    """The exact copied test tree, including data under src/tests/scripts.

    Prose/reports outside that declared tree are neither hashed nor made visible
    to these tests. Additional resource locations need explicit profile support.
    """
    return {name: value for name, value in baseline.items()
            if (copied_path(name) or name in RESOURCE_FILES) and (name.startswith(("src/", "tests/", "scripts/")) or name in
            {*RESOURCE_FILES, "pyproject.toml", "requirements-dev.lock", ".python-version",
             "conftest.py", "pytest.ini", "setup.cfg", "tox.ini"} or name.endswith(".py"))}


def copied_path(name):
    parts = [p.casefold() for p in name.split("/")]
    return not (set(parts) & (SENSITIVE_PARTS | {"harness-project.json"}) or parts[:2] == ["phase", "generated"] or
                any(p.startswith(".env") for p in parts) or parts[-1].endswith((".env", ".pem", ".key", ".pfx", ".p12")))


def prepare_profile(project, baseline):
    try:
        configuration = tomllib.loads((project / "pyproject.toml").read_text(encoding="utf-8"))
    except (OSError, ValueError) as exc:
        raise HarnessError("Self-test profile requires the harness pyproject.toml.") from exc
    if configuration.get("project", {}).get("name") != "development-tools-harness":
        raise HarnessError("The harness self-test profile requires a harness source checkout.")
    required = {*RESOURCE_FILES, "src/development_harness/__init__.py", "tests/conftest.py", "requirements-dev.lock"}
    missing = required - baseline.keys()
    if missing:
        raise HarnessError("Missing required self-test inputs: " + ", ".join(sorted(missing)))
    inputs = input_files(baseline)
    isolated, host = [], []
    for name in sorted(baseline):
        path = PurePosixPath(name)
        if not (path.suffix == ".py" and (path.name.startswith("test_") or path.name.endswith("_test.py"))):
            continue
        if name.startswith(("src/", "scripts/")):
            continue  # Controller helpers are code, not pytest modules.
        if "fixtures" in path.parts:
            continue  # These are data exercised by their owning tests.
        if name not in inputs:
            raise HarnessError("Self-test module is excluded by the resource policy: " + name)
        if not name.startswith("tests/unit/"):
            host.append({"path": name, "reason": "CLI, installation, recovery or OS integration; reviewed full host regression required"})
        elif path.name in HOST_UNIT_MODULES:
            host.append({"path": name, "reason": HOST_UNIT_MODULES[path.name]})
        else:
            isolated.append(name)
    if not isolated or not host:
        raise HarnessError("Self-test profile requires both isolated tests and separately reviewed host checks.")
    return {"name": SELF_TEST_PROFILE, "input_version": digest(inputs), "inputs": inputs,
            "resources": {name: baseline[name] for name in RESOURCE_FILES},
            "isolated_modules": isolated, "host_modules": host,
            "host_verification": "pending", "all_tests_complete": False,
            "required_manual_check": HOST_CHECK_ID}


def host_manual_check(plan):
    requirements = [item["id"] for item in plan["requirements"] if item["phase_id"] == plan["current_phase"]
                    and item["disposition"] in {"implement", "reuse"}]
    return {"id": HOST_CHECK_ID, "requirement_ids": requirements,
            "procedure": "Review the final B source and tests, run the separate reviewed-host full regression, and verify the combined self-test report matches the final input version. Record the report path and input version.",
            "expected": "Both isolated and reviewed-host checks pass on the same final inputs, with no omitted modules, skips, failures or stale evidence; runner A and protected records remain unchanged."}


def require_host_manual_check(checks, plan, manual):
    if not any(check.get("profile") == SELF_TEST_PROFILE for check in checks):
        return manual
    definition = host_manual_check(plan)
    existing = [item for item in manual if item["id"] == HOST_CHECK_ID]
    if existing and existing != [definition]:
        raise HarnessError("The mandatory harness host-regression check cannot be weakened or replaced.")
    return manual if existing else [*manual, definition]
