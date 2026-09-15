import json

import pytest

from development_harness.files import apply_write, snapshot
from development_harness.model import HarnessError, load_plan
from development_harness.store import Store


@pytest.mark.parametrize("name", ["../outside.py", "/absolute.py", "C:/file.py", ".git/config", ".GIT/config", ".harness-output/policy", "dir\\file.py", "NUL.txt"])
def test_unsafe_write_paths_rejected(workspace, name):
    harness, plan, path, save = workspace
    plan["tasks"][0]["writes"] = [{name: "bad"}]
    save()
    with pytest.raises(HarnessError):
        harness.prepare(path)


def test_unknown_adapter_fields_cannot_grant_approval(workspace):
    harness, plan, path, save = workspace
    plan["tasks"][0]["approve"] = True
    save()
    with pytest.raises(HarnessError):
        harness.prepare(path)


def test_cannot_write_plan_or_use_in_project_state(workspace):
    harness, plan, _, _ = workspace
    path = harness.project / "plan.json"
    plan["tasks"][0]["writes"] = [{"plan.json": "{}"}]
    path.write_text(json.dumps(plan))
    with pytest.raises(HarnessError, match="own approved plan"):
        harness.prepare(path)
    with pytest.raises(HarnessError, match="outside"):
        Store(harness.project, harness.project / "state")


def test_checked_write_preserves_file_changed_since_snapshot(workspace):
    harness, _, _, _ = workspace
    before = snapshot(harness.project)
    path = harness.project / "value.py"
    path.write_text("user edit")
    with pytest.raises(HarnessError, match="changed before write"):
        apply_write(harness.project, "value.py", "replacement", before["value.py"])
    assert path.read_text() == "user edit"


def test_unknown_fields_and_no_actual_test_command_rejected(workspace):
    _, plan, path, save = workspace
    plan["validation"][0]["kind"] = "command"
    save()
    with pytest.raises(HarnessError, match="actual pytest"):
        load_plan(path)


def test_case_alias_cannot_overwrite_the_wrong_baseline_entry(workspace):
    harness, plan, path, save = workspace
    plan["tasks"][0]["writes"] = [{"VALUE.py": "unexpected"}]
    save()
    with pytest.raises(HarnessError, match="casing differs"):
        harness.prepare(path)
    assert (harness.project / "value.py").read_text() == "VALUE = 0\n"


@pytest.mark.parametrize("field,value", [("review", [{}]), ("review", "pass")])
def test_malformed_review_input_has_actionable_error(workspace, field, value):
    _, plan, path, save = workspace
    plan["tasks"][0][field] = value
    save()
    with pytest.raises(HarnessError, match="review must"):
        load_plan(path)
