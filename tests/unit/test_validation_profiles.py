import copy
import json

import pytest

from development_harness.files import snapshot
from development_harness.model import HarnessError, digest, validate_checks
from development_harness.test_collection import complete_collection
from development_harness.validation_profiles import (HOST_CHECK_ID, RESOURCE_FILES, SELF_TEST_PROFILE,
    host_manual_check, prepare_profile, require_host_manual_check)
from development_harness.workflow import Workflow
from test_planning import fast_baseline, planning_workspace, ready


CHECK = {"kind": "pytest", "argv": ["{python}", "-m", "pytest", "-q"],
         "timeout": 300, "profile": SELF_TEST_PROFILE}


@pytest.fixture
def self_project(tmp_path):
    files = {"pyproject.toml": '[project]\nname="development-tools-harness"\n',
             "src/development_harness/__init__.py": "", "tests/conftest.py": "",
             "requirements-dev.lock": "", "tests/unit/test_rules.py": "def test_rules(): pass\n",
             "tests/integration/test_install.py": "def test_install(): pass\n"}
    files.update({name: "test resource" for name in RESOURCE_FILES})
    for name, content in files.items():
        path = tmp_path / name
        path.parent.mkdir(parents=True, exist_ok=True)
        path.write_text(content, encoding="utf-8")
    return tmp_path


@pytest.mark.parametrize("changes", [{"profile": "unknown"}, {"kind": "command"},
    {"argv": ["{python}", "-m", "pytest", "-k", "one"]},
    {"argv": ["{python}", "-m", "pytest", "tests/unit/test_one.py"]}])
def test_self_profile_cannot_be_silently_filtered(changes):
    with pytest.raises(HarnessError):
        validate_checks([CHECK | changes])


def test_profile_names_every_group_and_missing_required_data_fails(self_project):
    profile = prepare_profile(self_project, snapshot(self_project))
    assert profile["isolated_modules"] == ["tests/unit/test_rules.py"]
    assert profile["host_modules"][0]["path"] == "tests/integration/test_install.py"
    assert set(profile["resources"]) == set(RESOURCE_FILES)
    assert profile["all_tests_complete"] is False and profile["host_verification"] == "pending"
    (self_project / RESOURCE_FILES[0]).unlink()
    with pytest.raises(HarnessError, match="Missing required"):
        prepare_profile(self_project, snapshot(self_project))


def test_new_test_modules_and_root_configuration_change_input_identity(self_project):
    before = prepare_profile(self_project, snapshot(self_project))
    (self_project / "tests/unit/new_test.py").write_text("def test_new(): pass\n")
    (self_project / "conftest.py").write_text("# Affects all collection\n")
    after = prepare_profile(self_project, snapshot(self_project))
    assert "tests/unit/new_test.py" in after["isolated_modules"]
    assert after["input_version"] != before["input_version"]
    assert "conftest.py" in after["inputs"]


@pytest.mark.parametrize("field,value", [("deselected", ["x"]), ("skipped", ["x"]),
    ("collection_errors", ["x"]), ("passed", []), ("exit_status", 1)])
def test_collection_rejects_partial_execution(field, value):
    record = {"discovered": ["tests/unit/test_x.py::test_x"], "collected": ["tests/unit/test_x.py::test_x"], "passed": ["tests/unit/test_x.py::test_x"],
              "deselected": [], "failed": [], "skipped": [], "collection_errors": [], "exit_status": 0}
    assert complete_collection(record, ["tests/unit/test_x.py"], 1)
    assert not complete_collection(record | {field: value}, ["tests/unit/test_x.py"], 1)
    assert not complete_collection(record, ["tests/unit/test_x.py", "tests/unit/test_missing.py"], 1)


def test_workflow_automatically_pins_host_check_and_rejects_its_removal(planning_workspace, fast_baseline):
    planner, config = planning_workspace
    config["validation"] = [copy.deepcopy(CHECK)]
    ready(planner, config)
    planner.approve()
    workflow = Workflow(planner.project, planner.store.home)
    prepared = workflow.prepare(manual_checks=[])
    assert prepared["policy"]["manual_checks"] == [host_manual_check(prepared["plan"])]
    assert prepared["policy"]["manual_checks"][0]["id"] == HOST_CHECK_ID
    assert workflow.prepare(manual_checks=[])["id"] == prepared["id"]
    workflow.approve()
    corrupted = workflow.get()
    corrupted["policy"]["manual_checks"] = []
    corrupted["policy_hash"] = digest(corrupted["policy"])
    with pytest.raises(HarnessError, match="Mandatory"):
        workflow._check(corrupted)
    weakened = host_manual_check(prepared["plan"]) | {"expected": "anything passes"}
    with pytest.raises(HarnessError, match="cannot be weakened"):
        require_host_manual_check([CHECK], prepared["plan"], [weakened])
