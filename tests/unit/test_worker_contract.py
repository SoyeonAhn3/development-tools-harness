import copy
import json
import os

import pytest

from development_harness.model import HarnessError
from development_harness import worker_contract as contract


@pytest.fixture
def scoped(tmp_path):
    project = tmp_path / "project"
    project.mkdir()
    (project / "value.py").write_text("VALUE = 0\n", encoding="utf-8")
    (project / "spec.md").write_text("Return one.\n", encoding="utf-8")
    scope = contract.TaskScope(project, "T1", {"R1": "Return one."}, ["value.py", "new.py"], ["spec.md", "value.py"])
    proposal = {"task_id": "T1", "status": "changes", "summary": "Return one", "questions": [], "changes": [
        {"path": "value.py", "base_sha256": scope.baseline["value.py"], "content": "VALUE = 1\n"},
        {"path": "new.py", "base_sha256": "absent", "content": "# 한국어\n"}]}
    return scope, proposal


def test_controller_applies_only_expected_versions_and_records_bytes(scoped, tmp_path):
    scope, proposal = scoped
    result = contract.apply_proposal(scope, proposal, tmp_path / "patch")
    assert result["outcome"] == "applied"
    assert scope.project.joinpath("new.py").read_text(encoding="utf-8") == "# 한국어\n"
    assert scope.project.joinpath("spec.md").read_text() == "Return one.\n"
    assert result["after"] == scope.refresh().baseline
    assert json.loads((tmp_path / "patch/patch.json").read_text(encoding="utf-8")) == result


@pytest.mark.parametrize("path", ["outside.py", "../outside.py", ".git/config", "harness-project.json",
                                  "HARNESS-PROJECT.JSON", "Phase/Generated/plan.json", ".agents/policy.md", ".env", "secrets/key.txt"])
def test_entire_patch_is_rejected_before_any_out_of_scope_effect(scoped, tmp_path, path):
    scope, proposal = scoped
    proposal["changes"][1]["path"] = path
    with pytest.raises(HarnessError):
        contract.apply_proposal(scope, proposal, tmp_path / "patch")
    scope.check()
    assert not (tmp_path / "patch").exists()


@pytest.mark.parametrize("problem", ["wrong_hash", "duplicate", "status", "extra_field", "wrong_task"])
def test_invalid_model_change_never_starts_writing(scoped, tmp_path, problem):
    scope, proposal = scoped
    if problem == "wrong_hash":
        proposal["changes"][0]["base_sha256"] = "0" * 64
    elif problem == "duplicate":
        proposal["changes"].append(copy.deepcopy(proposal["changes"][0]))
    elif problem == "status":
        proposal["status"] = "unchanged"
    elif problem == "extra_field":
        proposal["command"] = "run arbitrary code"
    else:
        proposal["task_id"] = "unapproved-task"
    with pytest.raises(HarnessError):
        contract.apply_proposal(scope, proposal, tmp_path / "patch")
    scope.check()


def test_user_edit_is_preserved(scoped, tmp_path):
    scope, proposal = scoped
    (scope.project / "value.py").write_text("user edit\n")
    with pytest.raises(HarnessError, match="Unexpected file changes"):
        contract.apply_proposal(scope, proposal, tmp_path / "patch")
    assert (scope.project / "value.py").read_text() == "user edit\n"
    assert not (scope.project / "new.py").exists()


def test_partial_patch_is_recorded_without_overwriting_later_user_edit(scoped, tmp_path, monkeypatch):
    scope, proposal = scoped
    original = contract.apply_write
    def changed_after_first(*args):
        original(*args)
        (scope.project / "new.py").write_text("user-created file\n")
    monkeypatch.setattr(contract, "apply_write", changed_after_first)
    with pytest.raises(HarnessError, match="Unexpected file changes"):
        contract.apply_proposal(scope, proposal, tmp_path / "patch")
    record = json.loads((tmp_path / "patch/patch.json").read_text(encoding="utf-8"))
    assert record["outcome"] == "partial"
    assert len(record["applied"]) == 1
    assert (scope.project / "new.py").read_text() == "user-created file\n"


def test_hard_link_introduced_after_capture_is_rejected(scoped, tmp_path):
    scope, proposal = scoped
    os.link(scope.project / "value.py", tmp_path / "outside-link.py")
    with pytest.raises(HarnessError, match="Hard-linked"):
        contract.apply_proposal(scope, proposal, tmp_path / "patch")
    assert (tmp_path / "outside-link.py").read_text() == "VALUE = 0\n"


@pytest.mark.parametrize("path", ["harness-project.json", "Phase/Generated/plan.json", ".env", "config/production.env", ".codex/auth.json"])
def test_controller_cannot_define_protected_editable_scope(tmp_path, path):
    with pytest.raises(HarnessError):
        contract.TaskScope(tmp_path, "T1", {"R1": "work"}, [path], [])


@pytest.mark.parametrize("problem", ["required_pass", "optional_high", "unknown_requirement", "unknown_path", "no_evidence", "duplicate", "write_request"])
def test_inconsistent_or_unbounded_reviews_are_rejected(scoped, problem):
    scope, _ = scoped
    review = {"task_id": "T1", "verdict": "changes", "summary": "Wrong return value", "questions": [], "findings": [
        {"id": "F1", "requirement_id": "R1", "path": "value.py", "severity": "high", "required": True,
         "evidence": "VALUE is still zero", "recommendation": "Return one and verify it"}]}
    finding = review["findings"][0]
    if problem == "required_pass":
        review["verdict"] = "pass"
    elif problem == "optional_high":
        finding["required"] = False
    elif problem == "unknown_requirement":
        finding["requirement_id"] = "R9"
    elif problem == "unknown_path":
        finding["path"] = "outside.py"
    elif problem == "no_evidence":
        finding["evidence"] = ""
    elif problem == "duplicate":
        review["findings"].append(copy.deepcopy(finding))
    else:
        review["changes"] = []
    with pytest.raises(HarnessError):
        contract.validate_review(review, scope)


@pytest.mark.parametrize("role", ["developer", "reviewer"])
def test_total_response_budget_includes_questions(scoped, role):
    scope, _ = scoped
    value = {"task_id": "T1", "summary": "Need context",
             "questions": ["x" * 100000] * 10}
    if role == "developer":
        value.update(status="blocked", changes=[])
        validate = contract.validate_proposal
    else:
        value.update(verdict="blocked", findings=[])
        validate = contract.validate_review
    with pytest.raises(HarnessError, match="bounded output size"):
        validate(value, scope)
