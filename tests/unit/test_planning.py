import copy
import json
import os
from pathlib import Path
import sys
import time

import pytest

from development_harness.codex_adapter import parse_events
from development_harness.model import HarnessError
from development_harness.plan_schema import validate_plan
from development_harness.planning import Planning
from development_harness.project import load_project, read_json, source
from development_harness.runner import Harness


def words(text="Implement input validation"):
    return {"en": text, "ko": "입력 검증을 구현하고 확인한다"}


def example_plan():
    return {
        "overview": words(), "current_phase": "P1",
        "phases": [{"id": "P1", "title": words(), "goal": words(), "exit_criteria": words()}],
        "tasks": [{"id": "T1", "title": words(), "requirements": ["R1"], "paths": ["value.py"],
                   "acceptance": words(), "verification": words("Run pytest"), "depends_on": []}],
        "requirements": [{"id": "R1", "text": words(), "source_quote": "Reject negative values.",
                          "disposition": "implement", "phase_id": "P1", "verification": words(), "rationale": words()}],
        "code_context": [{"path": "value.py", "summary": words(), "evidence": "VALUE = 1", "kind": "inferred"}],
        "questions": [],
    }


@pytest.fixture
def planning_workspace(tmp_path):
    root = tmp_path / "planning project 한글"
    root.mkdir()
    (root / "spec.md").write_text("# Example\nReject negative values.\n", encoding="utf-8")
    (root / "value.py").write_text("VALUE = 1\n", encoding="utf-8")
    (root / "test_value.py").write_text("from value import VALUE\ndef test_value():\n    assert VALUE == 1\n")
    config = {"version": 1, "spec": "spec.md", "context": ["value.py"], "model": "test-model",
              "planner_timeout": 30,
              "validation": [{"argv": [sys.executable, "-m", "pytest", "-q"], "kind": "pytest", "timeout": 15}]}
    planner = Planning(root, tmp_path / "state")
    return planner, config


class StubAdapter:
    calls = 0
    response = None

    def __init__(self, model, directory):
        Path(directory).mkdir(parents=True, exist_ok=True)

    def verify(self):
        return {"boundary": "test stub"}

    def generate(self, prompt, schema, attempt, launched, timeout):
        StubAdapter.calls += 1
        attempt.update(outcome="running")
        launched(attempt)
        attempt.update(ended=time.time(), duration=0.01, outcome="responded")
        return copy.deepcopy(self.response or example_plan())


@pytest.fixture
def fast_baseline(monkeypatch):
    def check(config, project, directory, attempt, launched):
        attempt.update(outcome="passed", tests=1, ended=time.time(), duration=0.01)
        return attempt
    monkeypatch.setattr("development_harness.planning.validate", check)
    StubAdapter.calls, StubAdapter.response = 0, None


def ready(planner, config):
    planner.register(config)
    result = planner.plan(adapter_factory=StubAdapter)
    assert result["stage"] == "awaiting_plan_approval", result["reason"]
    return result


def test_plan_approval_is_idempotent_and_cannot_execute(planning_workspace, fast_baseline):
    planner, config = planning_workspace
    run = ready(planner, config)
    assert planner.plan(adapter_factory=StubAdapter)["id"] == run["id"]
    assert StubAdapter.calls == 1
    assert (planner.project / "value.py").read_text() == "VALUE = 1\n"
    assert planner.status()["actual_ai_call_attempts"] == 1
    first = planner.approve()
    assert first["approval"]["scope"] == "planning_only"
    assert planner.approve()["approval"] == first["approval"]
    assert planner.store.active() is None
    harness = Harness(planner.project, planner.store.home)
    for operation in (harness.execute, harness.approve, harness.accept, harness.status, harness.cancel):
        with pytest.raises(HarnessError, match="planning-only"):
            operation()


@pytest.mark.parametrize("change", ["spec.md", "value.py", "harness-project.json", "new-user-file.txt"])
def test_input_changes_preserved_and_block_approval(planning_workspace, fast_baseline, change):
    planner, config = planning_workspace
    ready(planner, config)
    (planner.project / change).write_text("user edit", encoding="utf-8")
    with pytest.raises(HarnessError, match="inputs changed"):
        planner.approve()
    assert (planner.project / change).read_text() == "user edit"


def test_modified_readable_plan_blocks_approval(planning_workspace, fast_baseline):
    planner, config = planning_workspace
    run = ready(planner, config)
    name = next(n for n in run["versions"][-1]["artifacts"] if n.endswith("Plan_ko.md"))
    (planner.project / name).write_text("user reviewed another version")
    with pytest.raises(HarnessError, match="artifact changed"):
        planner.approve()


def test_revision_preserves_history_and_requires_new_approval(planning_workspace, fast_baseline, tmp_path):
    planner, config = planning_workspace
    ready(planner, config)
    approval = planner.approve()["approval"]
    plan = example_plan()
    path = tmp_path / "edited.json"
    path.write_text(json.dumps(plan))
    assert planner.revise(path)["approval"] == approval
    plan["tasks"][0]["acceptance"] = words("Reject -1, accept 0")
    path.write_text(json.dumps(plan))
    revised = planner.revise(path)
    assert revised["approval"] is None
    assert len(revised["versions"]) == 2
    assert revised["versions"][0]["plan_hash"] == approval["plan_hash"]
    assert planner.approve()["approval"]["version"] == 2
    assert StubAdapter.calls == 1


def test_blocking_question_requires_resolution(planning_workspace, fast_baseline, tmp_path):
    planner, config = planning_workspace
    plan = example_plan()
    plan["questions"] = [{"id": "Q1", "text": words("Is zero allowed?"), "blocking": True}]
    StubAdapter.response = plan
    ready(planner, config)
    with pytest.raises(HarnessError, match="blocking questions"):
        planner.approve()
    plan["questions"] = []
    path = tmp_path / "resolved.json"
    path.write_text(json.dumps(plan))
    planner.revise(path)
    assert planner.approve()["stage"] == "plan_approved"


@pytest.mark.parametrize("outcome", ["failed", "no_tests", "unverified", "missing", "interrupted"])
def test_bad_baseline_never_calls_planner(planning_workspace, monkeypatch, outcome):
    planner, config = planning_workspace
    planner.register(config)
    def check(config, project, directory, attempt, launched):
        attempt.update(outcome=outcome)
    monkeypatch.setattr("development_harness.planning.validate", check)
    def no_adapter(*_):
        raise AssertionError("Planner must not run")
    stopped = planner.plan(adapter_factory=no_adapter)
    assert stopped["stage"] == "baseline_pending"
    assert stopped["reason"]
    assert planner.status()["actual_ai_call_attempts"] == 0


def test_baseline_file_mutation_is_not_accepted(planning_workspace, monkeypatch):
    planner, config = planning_workspace
    planner.register(config)
    def check(config, project, directory, attempt, launched):
        (project / "value.py").write_text("modified by test")
        attempt.update(outcome="passed")
    monkeypatch.setattr("development_harness.planning.validate", check)
    run = planner.plan(adapter_factory=StubAdapter)
    assert run["stage"] == "baseline_pending"
    assert "changed" in run["reason"]
    assert not run["baseline_evidence"]


def test_resume_after_interrupted_call_does_not_duplicate_finished_calls(planning_workspace, fast_baseline):
    planner, config = planning_workspace
    planner.register(config)
    class InterruptAdapter(StubAdapter):
        def generate(self, prompt, schema, attempt, launched, timeout):
            attempt.update(outcome="running")
            launched(attempt)
            raise KeyboardInterrupt
    stopped = planner.plan(adapter_factory=InterruptAdapter)
    assert stopped["attempts"][-1]["outcome"] == "interrupted"
    assert stopped["attempts"][-1]["duration"] is None
    completed = planner.plan(adapter_factory=StubAdapter)
    assert completed["stage"] == "awaiting_plan_approval"
    assert len([a for a in completed["attempts"] if a["role"] == "baseline_validation"]) == 1
    assert planner.status()["actual_ai_call_attempts"] == 2


def test_partial_publication_resumes_without_another_ai_call(planning_workspace, fast_baseline, monkeypatch):
    from development_harness import planning
    planner, config = planning_workspace
    planner.register(config)
    original = planning.save_new
    def interrupted(root, name, content):
        if name.endswith("Plan_ko.md"):
            raise KeyboardInterrupt
        original(root, name, content)
    monkeypatch.setattr(planning, "save_new", interrupted)
    stopped = planner.plan(adapter_factory=StubAdapter)
    assert stopped["pending_plan"]
    monkeypatch.setattr(planning, "save_new", original)
    assert planner.plan(adapter_factory=StubAdapter)["stage"] == "awaiting_plan_approval"
    assert StubAdapter.calls == 1


def test_permission_failure_prevents_live_attempt(planning_workspace, fast_baseline):
    planner, config = planning_workspace
    planner.register(config)
    class Denied(StubAdapter):
        def verify(self):
            raise HarnessError("permission probe failed")
    assert "permission" in planner.plan(adapter_factory=Denied)["reason"]
    assert planner.status()["actual_ai_call_attempts"] == 0


def test_interrupted_approved_revision_reclaims_ownership(planning_workspace, fast_baseline, monkeypatch, tmp_path):
    from development_harness import planning
    planner, config = planning_workspace
    ready(planner, config)
    planner.approve()
    revised = example_plan()
    revised["tasks"][0]["acceptance"] = words("Verify both zero and negative input")
    path = tmp_path / "revision.json"
    path.write_text(json.dumps(revised))
    original = planning.save_new
    def interrupted(root, name, content):
        if name.endswith("Plan_ko.md"):
            raise KeyboardInterrupt
        original(root, name, content)
    monkeypatch.setattr(planning, "save_new", interrupted)
    with pytest.raises(KeyboardInterrupt):
        planner.revise(path)
    assert planner.store.active()["stage"] == "planning"
    assert planner.get()["approval"] is None
    alternate = Planning(planner.project, tmp_path / "other-state")
    with pytest.raises(HarnessError, match="another state directory"):
        alternate.register(config)
    monkeypatch.setattr(planning, "save_new", original)
    result = planner.plan(adapter_factory=StubAdapter)
    assert len(result["versions"]) == 2
    assert result["stage"] == "awaiting_plan_approval"
    assert StubAdapter.calls == 1


def test_cancel_preserves_plans_and_cross_state_ownership(planning_workspace, fast_baseline, tmp_path):
    planner, config = planning_workspace
    ready(planner, config)
    alternate = Planning(planner.project, tmp_path / "alternate-state")
    with pytest.raises(HarnessError, match="another state directory"):
        alternate.register(config)
    artifacts = list((planner.project / "Phase/Generated").rglob("*.md"))
    planner.cancel()
    assert all(p.exists() for p in artifacts)
    alternate.register(config)


@pytest.mark.parametrize("path", ["../outside.md", "C:/outside.md", ".env", ".codex/auth.json", ".agents/skills/x/SKILL.md"])
def test_context_scope_rejects_unapproved_paths(planning_workspace, path):
    planner, config = planning_workspace
    config["context"] = [path]
    with pytest.raises(HarnessError):
        planner.register(config)


def test_hardlinked_context_is_rejected(planning_workspace, tmp_path):
    planner, config = planning_workspace
    outside = tmp_path / "outside.py"
    outside.write_text("private")
    os.link(outside, planner.project / "linked.py")
    config["context"] = ["linked.py"]
    with pytest.raises(HarnessError, match="Hard-linked"):
        planner.register(config)


def test_context_does_not_include_unselected_files(planning_workspace):
    planner, config = planning_workspace
    (planner.project / "unrelated.txt").write_text("unrelated information")
    planner.register(config)
    _, files = load_project(planner.project)
    assert [x["path"] for x in files] == ["spec.md", "value.py"]


@pytest.mark.parametrize("content", [b"\x00binary", b"\xff", ("sk-proj-" + "A" * 30).encode()])
def test_unsafe_context_content_is_rejected(planning_workspace, content):
    planner, _ = planning_workspace
    (planner.project / "value.py").write_bytes(content)
    with pytest.raises(HarnessError):
        source(planner.project, "value.py")


@pytest.mark.parametrize("mutation", [
    lambda p: p["requirements"][0].update(source_quote="Invented requirement"),
    lambda p: p["requirements"][0].update(phase_id="missing"),
    lambda p: p["requirements"][0].update(disposition="defer"),
    lambda p: p["tasks"][0].update(depends_on=["T1"]),
    lambda p: p["tasks"][0].update(requirements=["missing"]),
    lambda p: p["tasks"][0].update(paths=["../outside.py"]),
    lambda p: p["code_context"][0].update(evidence="nonexistent code"),
    lambda p: p.update(code_context=[]),
    lambda p: p.update(current_phase="missing"),
    lambda p: p.update(unknown="field"),
    lambda p: p["phases"].append(copy.deepcopy(p["phases"][0])),
])
def test_plan_semantics_reject_invalid_evidence_and_references(planning_workspace, mutation):
    planner, config = planning_workspace
    planner.register(config)
    _, files = load_project(planner.project)
    plan = example_plan()
    mutation(plan)
    with pytest.raises(HarnessError):
        validate_plan(plan, files)


def test_missing_baseline_evidence_blocks_approval(planning_workspace, fast_baseline):
    planner, config = planning_workspace
    run = ready(planner, config)
    run["baseline_evidence"] = []
    planner.store.save(run, "test_missing_evidence")
    with pytest.raises(HarnessError, match="baseline evidence"):
        planner.approve()


def test_json_duplicate_keys_are_rejected(tmp_path):
    p = tmp_path / "input.json"
    p.write_text('{"spec":"a","spec":"b"}')
    with pytest.raises(HarnessError, match="Duplicate"):
        read_json(p)


@pytest.mark.parametrize("event", [
    [], None, "text", {"type": "item.completed", "item": None},
    {"type": "item.completed", "item": {"type": "error"}},
    {"type": "turn.failed"},
    {"type": "item.completed", "item": {"type": "command_execution"}},
    {"type": "item.completed", "item": {"type": "agent_message", "text": "not JSON"}},
    {"type": "item.completed", "item": {"type": "agent_message", "text": {"a": 1}}},
    {"type": "item.completed", "item": {"type": "agent_message", "text": '{"a":1,"a":2}'}},
    {"type": "item.completed", "item": {"type": "agent_message", "text": '{"a":NaN}'}},
])
def test_untrusted_or_incomplete_provider_output_is_not_accepted(event):
    with pytest.raises(HarnessError):
        parse_events(json.dumps(event) + '\n' + json.dumps({"type": "turn.completed"}))
