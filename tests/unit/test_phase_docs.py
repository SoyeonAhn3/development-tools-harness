import copy
import json
from pathlib import Path
import shutil

import pytest

from development_harness import phase_docs
from development_harness.model import HarnessError
from development_harness.planning import build_prompt
from development_harness.project import load_project
from test_planning import (StubAdapter, example_plan, fast_baseline, planning_workspace, ready)


@pytest.fixture
def local_skill(tmp_path, monkeypatch):
    destination = tmp_path / "runner-skill"
    shutil.copytree(phase_docs.skill_directory(), destination)
    monkeypatch.setattr(phase_docs, "skill_directory", lambda: destination)
    return destination


def phase_artifact(run):
    return next(name for name in run["versions"][-1]["artifacts"]
                if Path(name).name.startswith("Phase1_"))


def test_real_writing_resources_reach_adapter_and_version_records(planning_workspace, fast_baseline):
    planner, config = planning_workspace
    planner.register(config)
    captured = {}
    class Capture(StubAdapter):
        def __init__(self, model, directory):
            super().__init__(model, directory)
            captured["directory"] = Path(directory)

        def generate(self, prompt, schema, attempt, launched, timeout):
            captured.update(prompt=prompt, schema=schema)
            return super().generate(prompt, schema, attempt, launched, timeout)

    run = planner.plan(adapter_factory=Capture)
    profile = run["writing_profile"]
    # Inspect the actual serialized packet, not just a skill name in the prompt.
    packet = json.loads(captured["prompt"].split("\n", 1)[1].split("\n\n", 1)[0])
    assert packet["writing_rules"] == profile
    assert "technology" in captured["schema"]["required"]
    assert json.loads((captured["directory"] / "writing-profile.json").read_text(encoding="utf-8")) == profile
    version = run["versions"][-1]
    assert version["writing_profile_hash"] == profile["sha256"]
    assert run["attempts"][-1]["writing_profile_hash"] == profile["sha256"]
    document = (planner.project / phase_artifact(run)).read_text(encoding="utf-8")
    assert document.index("## Tasks & Verification") < document.index("\n---\n") < document.index("## Task 및 검증")
    assert "T1" in document and "R1" in document and "Python and pytest" in document
    assert planner.approve()["approval"]["writing_profile_hash"] == profile["sha256"]
    assert planner.status()["writing_profile"]["files"]["SKILL.md"] == profile["files"]["SKILL.md"]["sha256"]


def test_template_changes_apply_to_new_runs_but_not_resume_or_revisions(
        planning_workspace, fast_baseline, local_skill, tmp_path):
    planner, config = planning_workspace
    first = planner.register(config)
    template = local_skill / "references/phase-template.md"
    template.write_text(template.read_text(encoding="utf-8").replace(
        "## Tasks & Verification", "## Project Work and Evidence"), encoding="utf-8")
    # Resume uses the profile already fixed at registration, not current disk contents.
    run = planner.plan(adapter_factory=StubAdapter)
    original_hash = run["writing_profile"]["sha256"]
    assert "## Tasks & Verification" in (planner.project / phase_artifact(run)).read_text(encoding="utf-8")
    revised = copy.deepcopy(run["versions"][-1]["plan"])
    revised["tasks"][0]["acceptance"]["en"] = "Reject -1 and preserve zero"
    revision = tmp_path / "revision.json"
    revision.write_text(json.dumps(revised), encoding="utf-8")
    run = planner.revise(revision)
    assert run["writing_profile"]["sha256"] == original_hash
    assert "## Tasks & Verification" in (planner.project / phase_artifact(run)).read_text(encoding="utf-8")
    assert "Reject -1 and preserve zero" in (planner.project / phase_artifact(run)).read_text(encoding="utf-8")
    planner.cancel()
    second = ready(planner, config)
    assert second["id"] != first["id"]
    assert second["writing_profile"]["sha256"] != original_hash
    assert "## Project Work and Evidence" in (planner.project / phase_artifact(second)).read_text(encoding="utf-8")


@pytest.mark.parametrize("damage", ["missing", "slot", "duplicate_block", "version"])
def test_invalid_skill_stops_registration_before_project_write(planning_workspace, local_skill, damage):
    planner, config = planning_workspace
    template = local_skill / "references/phase-template.md"
    if damage == "missing":
        template.unlink()
    elif damage == "version":
        skill = local_skill / "SKILL.md"
        skill.write_text(skill.read_text(encoding="utf-8").replace('  version: "1.1"', ''), encoding="utf-8")
    elif damage == "slot":
        template.write_text(template.read_text(encoding="utf-8").replace("{{tasks}}", "{{unknown}}"), encoding="utf-8")
    else:
        template.write_text(template.read_text(encoding="utf-8") + "\n<!-- harness:phase:en -->", encoding="utf-8")
    with pytest.raises(HarnessError, match="phase-doc"):
        planner.register(config)
    assert not (planner.project / "harness-project.json").exists()


@pytest.mark.parametrize("artifact", ["phase", "profile"])
def test_editing_skill_generated_artifacts_blocks_approval(planning_workspace, fast_baseline, artifact):
    planner, config = planning_workspace
    run = ready(planner, config)
    name = phase_artifact(run) if artifact == "phase" else next(
        n for n in run["versions"][-1]["artifacts"] if n.endswith("writing-profile.json"))
    (planner.project / name).write_text("changed after generation", encoding="utf-8")
    with pytest.raises(HarnessError, match="artifact changed"):
        planner.approve()


def test_corrupted_recorded_rules_stop_before_any_ai_attempt(planning_workspace, fast_baseline):
    planner, config = planning_workspace
    run = planner.register(config)
    run["writing_profile"]["files"]["SKILL.md"]["text"] += "changed"
    planner.store.save(run, "test_corruption")
    with pytest.raises(HarnessError, match="digest mismatch"):
        planner.plan(adapter_factory=StubAdapter)
    assert StubAdapter.calls == 0


def test_target_project_skill_is_not_loaded(planning_workspace, fast_baseline):
    planner, config = planning_workspace
    target = planner.project / ".agents/skills/phase-doc/SKILL.md"
    target.parent.mkdir(parents=True)
    target.write_text("TARGET_SKILL_MUST_NOT_BECOME_CONTROLLER_RULES", encoding="utf-8")
    run = planner.register(config)
    _, files = load_project(planner.project)
    prompt = build_prompt(files, run["writing_profile"])
    assert "TARGET_SKILL_MUST_NOT_BECOME_CONTROLLER_RULES" not in prompt
    assert run["writing_profile"] == phase_docs.load_profile()


def test_legacy_runs_keep_original_schema_artifacts_and_approval(planning_workspace, fast_baseline, monkeypatch, tmp_path):
    planner, config = planning_workspace
    run = planner.register(config)
    run.pop("writing_profile")
    planner.store.save(run, "legacy_fixture")
    # Loading/installing new skills is not a prerequisite for old records.
    monkeypatch.setattr(phase_docs, "skill_directory", lambda: tmp_path / "missing")
    run = planner.plan(adapter_factory=StubAdapter)
    assert run["stage"] == "awaiting_plan_approval", run["reason"]
    assert {Path(p).name for p in run["versions"][0]["artifacts"]} == {"plan.json", "Plan.md", "Plan_ko.md"}
    original = {p: (planner.project / p).read_bytes() for p in run["versions"][0]["artifacts"]}
    approval = planner.approve()["approval"]
    assert "writing_profile_hash" not in approval
    revision = tmp_path / "legacy-revision.json"
    plan = example_plan(skill=False)
    revision.write_text(json.dumps(plan), encoding="utf-8")
    assert planner.revise(revision)["approval"] == approval
    plan["tasks"][0]["title"]["en"] = "Revised legacy task"
    revision.write_text(json.dumps(plan), encoding="utf-8")
    assert planner.revise(revision)["versions"][-1]["version"] == 2
    assert all((planner.project / p).read_bytes() == body for p, body in original.items())
    assert "writing_profile" not in planner.status()


def test_current_phase_details_and_future_outline_stay_bilingual():
    plan = example_plan()
    plan["phases"].append({"id": "P2", "title": {"en": "Delivery", "ko": "전달"},
                           "goal": {"en": "Deliver later", "ko": "후속 전달"},
                           "exit_criteria": {"en": "Accepted delivery", "ko": "전달 인수"}})
    plan["requirements"][0]["source_quote"] = "Read [reference](original.md)."
    documents = phase_docs.render_documents(plan, phase_docs.load_profile(), 1789956248)
    current = documents["Phase1_ImplementInputValidation.md"]
    later = documents["Phase2_Delivery.md"]
    assert "T1" in current and "T1" not in later
    assert "후속 전달" in later and "Deliver later" in later
    assert "```text\nRead [reference](original.md).\n```" in current
    assert "Phase2_Delivery.md" in documents["Plan.md"]
    assert "Phase2_Delivery.md" in documents["Plan_ko.md"]


def test_project_text_is_not_executed_as_template_slots():
    plan = example_plan()
    plan["tasks"][0]["acceptance"]["en"] = "Keep {{profile_hash}} as literal project text"
    documents = phase_docs.render_documents(plan, phase_docs.load_profile(), 1789956248)
    assert "Keep {{profile_hash}} as literal project text" in documents["Phase1_ImplementInputValidation.md"]


def test_conflicting_document_names_fail_before_publication(planning_workspace, fast_baseline):
    planner, config = planning_workspace
    plan = example_plan()
    duplicate = copy.deepcopy(plan["phases"][0])
    duplicate["id"] = "Phase1"
    plan["phases"].append(duplicate)
    StubAdapter.response = plan
    planner.register(config)
    result = planner.plan(adapter_factory=StubAdapter)
    assert "collide" in result["reason"]
    assert not result["versions"]
    assert not (planner.project / "Phase/Generated").exists()


def test_partial_skill_document_publication_recovers_with_pinned_rules(
        planning_workspace, fast_baseline, monkeypatch, local_skill):
    from development_harness import planning
    planner, config = planning_workspace
    planner.register(config)
    save = planning.save_new
    def interrupt(root, name, content):
        if name.endswith("writing-profile.json"):
            raise KeyboardInterrupt
        save(root, name, content)
    monkeypatch.setattr(planning, "save_new", interrupt)
    assert planner.plan(adapter_factory=StubAdapter)["pending_plan"]
    # Existing records must not need the current template after dispatch/publication.
    (local_skill / "references/phase-template.md").unlink()
    monkeypatch.setattr(planning, "save_new", save)
    run = planner.plan(adapter_factory=StubAdapter)
    assert run["stage"] == "awaiting_plan_approval"
    assert StubAdapter.calls == 1
    assert "inspection_error" not in planner.status()
