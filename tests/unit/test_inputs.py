import json
import os
from contextlib import contextmanager

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


@pytest.mark.parametrize("name", ["value.py", "unrelated.txt"])
def test_prepare_rejects_hard_links_and_preserves_external_files(workspace, tmp_path, name):
    harness, _, path, _ = workspace
    external = tmp_path / "user-owned.txt"
    external.write_text("VALUE = 0\n")
    linked = harness.project / name
    linked.unlink(missing_ok=True)
    os.link(external, linked)
    with pytest.raises(HarnessError, match="Hard-linked"):
        harness.prepare(path)
    assert external.read_text() == "VALUE = 0\n"
    assert harness.store.active() is None


def test_hard_link_added_after_approval_stops_before_writing(workspace, tmp_path):
    harness, _, path, _ = workspace
    harness.prepare(path)
    harness.approve()
    external = tmp_path / "user-owned.txt"
    os.link(harness.project / "value.py", external)
    with pytest.raises(HarnessError, match="Hard-linked"):
        harness.execute()
    assert external.read_text() == "VALUE = 0\n"
    assert harness.store.get()["attempts"] == []


def test_opened_file_check_blocks_hard_link_added_after_path_inspection(workspace, tmp_path, monkeypatch):
    from development_harness import files

    harness, _, _, _ = workspace
    baseline = snapshot(harness.project)
    external = tmp_path / "user-owned.txt"
    original = files.exclusive_file

    @contextmanager
    def add_link_before_open(path, exists):
        os.link(path, external)
        with original(path, exists) as stream:
            yield stream

    monkeypatch.setattr(files, "exclusive_file", add_link_before_open)
    with pytest.raises(HarnessError, match="Hard-linked"):
        apply_write(harness.project, "value.py", "replacement", baseline["value.py"])
    assert external.read_text() == "VALUE = 0\n"
