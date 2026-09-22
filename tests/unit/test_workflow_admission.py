"""Admission tests exercise approved artifacts without an AI service call."""

import copy
import json
from pathlib import Path

import pytest

from development_harness import phase_docs
from development_harness.files import snapshot
from development_harness.model import HarnessError, digest
from development_harness.runner import Harness
from development_harness.workflow import Workflow
from test_planning import (StubAdapter, example_plan, fast_baseline, planning_workspace, ready, words)


@pytest.fixture
def approved(planning_workspace, fast_baseline):
    planner, config = planning_workspace
    ready(planner, config)
    source = planner.approve()
    return planner, source, Workflow(planner.project, planner.store.home)


def test_admission_and_approval_are_separate_idempotent_and_do_not_dispatch(approved, monkeypatch):
    planner, source, workflow = approved
    before = snapshot(planner.project)
    source_before = copy.deepcopy(source)
    monkeypatch.setattr("development_harness.workers.CodexWorker.invoke",
                        lambda *args, **kwargs: pytest.fail("Admission cannot dispatch an AI worker"))
    run = workflow.prepare()
    assert run["stage"] == "awaiting_execution_approval"
    assert run["approval"] is None
    assert run["planning_approval"]["scope"] == "planning_only"
    assert run["planning_run_id"] == source["id"]
    assert run["input_hash"] == source["input_hash"]
    assert run["content_version"] == digest(before)
    assert run["content_version"] != run["input_hash"]  # Plans are versioned separately in planning.
    assert run["policy"]["validation"] == source["config"]["validation"]
    assert run["waits"][0]["ended"] is run["waits"][0]["duration"] is None
    assert workflow.prepare()["id"] == run["id"]
    first = workflow.approve()
    event_count = len(workflow.store.events(run["id"]))
    assert first["stage"] == "execution_ready"
    assert first["approval"]["scope"] == "execution"
    assert first["approval"]["content_version"] == digest(before)
    assert first["waits"][0]["duration"] >= 0
    assert workflow.approve() == first
    assert len(workflow.store.events(run["id"])) == event_count
    assert workflow.prepare()["id"] == first["id"]
    assert workflow.status()["execution_authorized"] is True
    assert workflow.status()["workflow_execution_enabled"] is True
    assert workflow.status()["orchestration_available"] is True
    assert workflow.status()["attempts"] == []
    assert snapshot(planner.project) == before
    assert planner.get() == source_before
    assert planner.status()["id"] == source["id"]
    assert planner.approve()["approval"] == source["approval"]
    assert StubAdapter.calls == 1  # Only the injected planning transport ran.


def test_unapproved_planning_cannot_create_workflow(planning_workspace, fast_baseline):
    planner, config = planning_workspace
    ready(planner, config)
    with pytest.raises(HarnessError, match="approved planning"):
        Workflow(planner.project, planner.store.home).prepare()
    assert planner.store.get()["kind"] == "planning"


@pytest.mark.parametrize("field,value", [("scope", "execution"), ("version", 99),
                                         ("plan_hash", "stale"), ("input_hash", "stale"),
                                         ("writing_profile_hash", "stale")])
def test_stale_planning_authorization_cannot_admit(approved, field, value):
    planner, source, workflow = approved
    source["approval"][field] = value
    planner.store.save(source, "test_corrupted_approval")
    with pytest.raises(HarnessError, match="approval"):
        workflow.prepare()
    assert planner.store.get()["id"] == source["id"]


@pytest.mark.parametrize("name", ["spec.md", "value.py", "harness-project.json", "new-user-file.txt"])
def test_changed_starting_content_blocks_preparation_without_overwrite(approved, name):
    planner, _, workflow = approved
    (planner.project / name).write_text("user change\n", encoding="utf-8")
    before = snapshot(planner.project)
    with pytest.raises(HarnessError):
        workflow.prepare()
    assert snapshot(planner.project) == before


@pytest.mark.parametrize("artifact", ["plan.json", "Plan_ko.md", "writing-profile.json"])
def test_changed_reviewed_artifact_blocks_admission(approved, artifact):
    planner, source, workflow = approved
    name = next(name for name in source["versions"][-1]["artifacts"] if Path(name).name == artifact)
    (planner.project / name).write_text("changed reviewed artifact\n", encoding="utf-8")
    with pytest.raises(HarnessError, match="artifact changed"):
        workflow.prepare()
    assert (planner.project / name).read_text(encoding="utf-8") == "changed reviewed artifact\n"


def test_missing_baseline_evidence_blocks_admission(approved):
    planner, source, workflow = approved
    source["baseline_evidence"] = []
    planner.store.save(source, "test_removed_baseline")
    with pytest.raises(HarnessError, match="baseline evidence"):
        workflow.prepare()


def test_pinned_profile_is_used_even_if_installed_skill_is_unavailable(approved, monkeypatch, tmp_path):
    _, source, workflow = approved
    monkeypatch.setattr(phase_docs, "skill_directory", lambda: tmp_path / "missing-new-installation")
    run = workflow.prepare()
    assert run["writing_profile_hash"] == source["writing_profile"]["sha256"]
    workflow.approve()


def test_corrupted_pinned_profile_blocks_admission(approved):
    planner, source, workflow = approved
    source["writing_profile"]["files"]["SKILL.md"]["text"] += "corruption"
    planner.store.save(source, "test_corrupted_profile")
    with pytest.raises(HarnessError, match="writing rules"):
        workflow.prepare()


def test_legacy_plan_without_writing_profile_can_be_admitted(planning_workspace, fast_baseline):
    planner, config = planning_workspace
    source = planner.register(config)
    source.pop("writing_profile")
    planner.store.save(source, "test_legacy_planning")
    planner.plan(adapter_factory=StubAdapter)
    source = planner.approve()
    workflow = Workflow(planner.project, planner.store.home)
    run = workflow.prepare()
    assert run["writing_profile_hash"] is None
    assert "writing_profile_hash" not in source["approval"]
    assert workflow.approve()["stage"] == "execution_ready"


@pytest.mark.parametrize("argv,kind", [
    (["other-python.exe", "-m", "pytest"], "pytest"),
    (["{python}", "-m", "pytest", "--capture=fd"], "pytest"),
    (["{python}", "-m", "pytest", "--basetemp", "C:/outside"], "pytest"),
    (["cmd.exe", "/c", "echo", "unsupported"], "command"),
])
def test_planning_compatible_but_unisolated_validation_blocks_admission(
        planning_workspace, fast_baseline, argv, kind):
    planner, config = planning_workspace
    if kind == "command":
        config["validation"].append({"argv": argv, "kind": kind, "timeout": 15})
    else:
        config["validation"][0].update(argv=argv, kind=kind)
    ready(planner, config)
    planner.approve()
    with pytest.raises(HarnessError, match="pytest"):
        Workflow(planner.project, planner.store.home).prepare()


@pytest.mark.parametrize("paths", [["spec.md"], [".env"], ["HARNESS-PROJECT.JSON"],
                                   ["Phase/Generated/new.py"], ["VALUE.py"], ["value.py", "VALUE.py"]])
def test_proposed_paths_do_not_override_worker_scope_protection(
        planning_workspace, fast_baseline, paths):
    planner, config = planning_workspace
    plan = example_plan()
    plan["tasks"][0]["paths"] = paths
    StubAdapter.response = plan
    ready(planner, config)
    planner.approve()
    before = snapshot(planner.project)
    with pytest.raises(HarnessError):
        Workflow(planner.project, planner.store.home).prepare()
    assert snapshot(planner.project) == before


def test_forged_approval_cannot_bypass_blocking_questions(planning_workspace, fast_baseline):
    planner, config = planning_workspace
    plan = example_plan()
    plan["questions"] = [{"id": "Q1", "text": words("Clarify input policy"), "blocking": True}]
    StubAdapter.response = plan
    source = ready(planner, config)
    version = source["versions"][-1]
    source.update(stage="plan_approved", approval={
        "scope": "planning_only", "version": version["version"], "plan_hash": version["plan_hash"],
        "input_hash": source["input_hash"], "writing_profile_hash": source["writing_profile"]["sha256"],
        "at": source["created"],
    })
    planner.store.save(source, "test_forged_approval")
    with pytest.raises(HarnessError, match="Blocking"):
        Workflow(planner.project, planner.store.home).prepare()


def test_admission_includes_only_current_phase_tasks_and_preserves_dependency_order(
        planning_workspace, fast_baseline):
    planner, config = planning_workspace
    plan = example_plan()
    plan["phases"].append({"id": "P2", "title": words("Later phase"), "goal": words(), "exit_criteria": words()})
    later = copy.deepcopy(plan["requirements"][0])
    later.update(id="R2", phase_id="P2", disposition="defer")
    plan["requirements"].append(later)
    second = copy.deepcopy(plan["tasks"][0])
    second.update(id="T2", paths=["new.py"], depends_on=["T1"])
    plan["tasks"].append(second)
    StubAdapter.response = plan
    ready(planner, config)
    planner.approve()
    workflow = Workflow(planner.project, planner.store.home)
    run = workflow.prepare()
    assert run["phase_id"] == "P1"
    assert [task["id"] for task in run["tasks"]] == ["T1", "T2"]
    assert run["tasks"][1]["depends_on"] == ["T1"]
    assert all("R2" not in task["requirements"] for task in run["tasks"])
    assert not (planner.project / "new.py").exists()
    workflow.approve()
    with pytest.raises(HarnessError, match="outside"):
        workflow.invoke("P2-T1", "developer", worker_factory=lambda *args: pytest.fail("No worker"))
    assert workflow.get()["attempts"] == []


def test_explicit_old_planning_run_cannot_override_latest_plan(approved):
    planner, source, workflow = approved
    ready(planner, source["config"])
    latest = planner.approve()
    with pytest.raises(HarnessError, match="latest planning"):
        workflow.prepare(source["id"])
    assert workflow.prepare(latest["id"])["planning_run_id"] == latest["id"]


@pytest.mark.parametrize("change", ["code", "config", "policy", "content_version", "baseline", "plan", "profile"])
def test_prepared_versions_are_rechecked_before_execution_approval(approved, change):
    planner, _, workflow = approved
    run = workflow.prepare()
    if change == "code":
        (planner.project / "value.py").write_text("user change\n")
    elif change == "config":
        path = planner.project / "harness-project.json"
        config = json.loads(path.read_text())
        config["validation"][0]["timeout"] += 1
        path.write_text(json.dumps(config))
    else:
        if change == "policy":
            run["policy"]["max_corrections"] = 9
        elif change == "content_version":
            run["content_version"] = "stale"
        elif change == "baseline":
            run["baseline"]["value.py"] = "stale"
        elif change == "plan":
            run["plan"]["tasks"][0]["acceptance"]["en"] = "Unreviewed requirements"
        else:
            run["writing_profile_hash"] = "stale"
        workflow.store.save(run, "test_changed_prepared_record")
    before = snapshot(planner.project)
    with pytest.raises(HarnessError):
        workflow.approve()
    assert workflow.get()["approval"] is None
    assert "inspection_error" in workflow.status()
    assert snapshot(planner.project) == before


def test_fake_harness_cannot_execute_or_accept_workflow(approved):
    planner, _, workflow = approved
    workflow.prepare()
    workflow.approve()
    harness = Harness(planner.project, planner.store.home)
    for action in (harness.execute, harness.approve, harness.accept, harness.status, harness.cancel):
        with pytest.raises(HarnessError, match="workflow"):
            action()
    assert workflow.get()["stage"] == "execution_ready"
    assert workflow.get()["attempts"] == []


def test_invocation_without_execution_authorization_never_prepares_attempt(approved):
    _, _, workflow = approved
    workflow.prepare()
    with pytest.raises(HarnessError, match="authorization"):
        workflow.invoke("T1", "developer", worker_factory=lambda *args: pytest.fail("No worker"))
    assert workflow.get()["attempts"] == []


def test_active_workflow_blocks_new_planning_and_alternate_state(approved, tmp_path):
    planner, source, workflow = approved
    run = workflow.prepare()
    with pytest.raises(HarnessError, match="unfinished run"):
        planner.register(source["config"])
    with pytest.raises(HarnessError, match="another state directory"):
        Workflow(planner.project, tmp_path / "alternate-state").prepare()
    assert workflow.store.active()["id"] == run["id"]


def test_cancel_preserves_evidence_and_user_edits_and_cannot_be_approved(approved):
    planner, source, workflow = approved
    run = workflow.prepare()
    (planner.project / "value.py").write_text("user edit after admission\n")
    before = snapshot(planner.project)
    cancelled = workflow.cancel()
    assert cancelled["stage"] == "cancelled"
    assert cancelled["waits"][0]["duration"] >= 0
    event_count = len(workflow.store.events(run["id"]))
    assert workflow.cancel() == cancelled
    assert len(workflow.store.events(run["id"])) == event_count
    assert workflow.store.active() is None
    with pytest.raises(HarnessError):
        workflow.approve()
    assert planner.get()["id"] == source["id"]
    assert snapshot(planner.project) == before


@pytest.mark.parametrize("limit", [0, 2, 5])
def test_correction_policy_is_pinned_before_approval(approved, limit):
    _, _, workflow = approved
    run = workflow.prepare(max_corrections=limit)
    assert workflow.status()["max_corrections"] == limit
    admitted = workflow.approve()
    assert admitted["approval"]["policy_hash"] == digest(run["policy"])
    assert workflow.prepare() == admitted
    assert workflow.prepare(max_corrections=limit) == admitted
    with pytest.raises(HarnessError, match="pinned"):
        workflow.prepare(max_corrections=limit + 1)
    assert workflow.get() == admitted


@pytest.mark.parametrize("limit", [-1, 101, True, 1.5])
def test_invalid_correction_limit_creates_no_workflow(approved, limit):
    _, source, workflow = approved
    with pytest.raises(HarnessError, match="integer"):
        workflow.prepare(max_corrections=limit)
    assert workflow.store.get()["id"] == source["id"]


def test_execution_requires_separate_approval_and_valid_boundary_limit(approved):
    _, _, workflow = approved
    workflow.prepare()
    no_worker = lambda *args: pytest.fail("No worker may start")
    with pytest.raises(HarnessError, match="approval"):
        workflow.execute(worker_factory=no_worker)
    workflow.approve()
    for steps in (0, -1, True, 1.5):
        with pytest.raises(HarnessError, match="positive integer"):
            workflow.execute(worker_factory=no_worker, steps=steps)
    assert workflow.get()["attempts"] == []
