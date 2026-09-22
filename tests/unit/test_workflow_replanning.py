"""Fresh input admission after requirements feedback without AI or file writes."""

import copy
import json
from pathlib import Path
import sqlite3
import subprocess
import sys

import pytest

from development_harness.files import snapshot
from development_harness.model import HarnessError, digest
from development_harness.planning import Planning
from development_harness.processes import identity
from development_harness.project import content_baseline
from test_workflow_admission import approved
from test_planning import fast_baseline, planning_workspace


@pytest.fixture
def replanning(approved):
    planner, source, workflow = approved
    workflow.prepare()
    run = workflow.approve()
    run.update(stage="replanning_required", reason="Requirements feedback needs a new plan.",
               feedback=[{"id": "feedback-1", "kind": "requirements", "text": "Also accept decimal values.\nKeep existing behavior.",
                          "task_id": None, "phase_id": run["phase_id"], "plan_hash": run["plan_hash"],
                          "content_version": run["content_version"], "policy_hash": run["policy_hash"],
                          "received_at": 1, "routing_outcome": "replanning_required", "outcome": "replanning_required",
                          "history": [{"outcome": "replanning_required", "at": 1}], "previous_completion": None}])
    run["execution"] = {"in_flight": False, "patch_pending": None, "active_step": None}
    workflow.store.save(run, "test_requirements_feedback")
    return planner, source, workflow, copy.deepcopy(run)


def test_replan_admits_changed_current_inputs_and_preserves_historical_approval(replanning):
    planner, source, workflow, original = replanning
    (planner.project / "value.py").write_text("VALUE = 2\n# User code preserved.\n", encoding="utf-8")
    (planner.project / "spec.md").write_text("Reject negative values.\nAlso accept decimal values.\n", encoding="utf-8")
    (planner.project / "notes.txt").write_text("Keep these user notes.\n", encoding="utf-8")
    before = snapshot(planner.project)
    replacement = planner.replan()
    previous = workflow.get()
    assert replacement["kind"] == "planning" and replacement["stage"] == "baseline_pending"
    assert replacement["id"] not in {source["id"], original["id"]}
    assert replacement["approval"] is None
    assert replacement["attempts"] == replacement["baseline_evidence"] == replacement["versions"] == []
    assert replacement["baseline"] == content_baseline(planner.project)
    assert replacement["input_hash"] == digest(replacement["baseline"]) != source["input_hash"]
    assert replacement["writing_profile"]["sha256"]
    assert replacement["feedback_source"] == {"workflow_run_id": original["id"], "planning_run_id": source["id"],
                                               "feedback_ids": ["feedback-1"]}
    assert planner.store.active()["id"] == replacement["id"]
    assert previous["stage"] == "superseded"
    assert previous["approval"] == original["approval"]
    assert previous["planning_approval"] == original["planning_approval"]
    feedback = previous["feedback"][0]
    assert feedback["text"] == original["feedback"][0]["text"]
    assert feedback["routing_outcome"] == "replanning_required"
    assert feedback["outcome"] == "replanning_started"
    assert feedback["history"][:-1] == original["feedback"][0]["history"]
    assert feedback["history"][-1]["planning_run_id"] == replacement["id"]
    assert planner.store.get(source["id"]) == source
    assert snapshot(planner.project) == before
    assert planner._check(replacement)
    assert planner.store.events(original["id"])[-1]["kind"] == "workflow_superseded"
    assert planner.store.events(replacement["id"])[-1]["kind"] == "replanning_registered"


def test_replan_is_idempotent_and_new_plan_still_requires_baseline_and_approval(replanning):
    planner, _, workflow, original = replanning
    replacement = planner.replan()
    old_events = planner.store.events(original["id"])
    new_events = planner.store.events(replacement["id"])
    assert Planning(planner.project, planner.store.home).replan() == replacement
    assert planner.store.events(original["id"]) == old_events
    assert planner.store.events(replacement["id"]) == new_events
    with pytest.raises(HarnessError, match="baseline evidence|No reviewed plan"):
        planner.approve()
    with pytest.raises(HarnessError):
        workflow.prepare()
    with pytest.raises(HarnessError, match="unfinished run"):
        planner.register(replacement["config"])


@pytest.mark.parametrize("damage", ["stage", "feedback", "in_flight", "patch_pending", "active_step", "unfinished", "uncertain", "live_process"])
def test_replan_requires_quiescent_owned_workflow_and_explicit_feedback(replanning, damage):
    planner, _, workflow, run = replanning
    if damage == "stage":
        run["stage"] = "technically_complete"
    elif damage == "feedback":
        run["feedback"] = []
    elif damage in {"in_flight", "patch_pending", "active_step"}:
        run["execution"][damage] = True
    else:
        run["attempts"] = [{"id": "unsettled", "role": "developer", "task_id": "T1", "outcome": "prepared",
                            "journal_phases": {}, "dispatch_status": "not_sent"}]
        if damage == "uncertain":
            run["attempts"][0].update(dispatch_status="uncertain", journal_phases={"dispatch_intent": 1})
        elif damage == "live_process":
            run["attempts"][0]["process"] = identity()
    workflow.store.save(run, "test_replan_blocker")
    before = snapshot(planner.project)
    events = planner.store.events(run["id"])
    with pytest.raises(HarnessError):
        planner.replan()
    assert workflow.get() == run
    assert planner.store.events(run["id"]) == events
    assert planner.store.active()["id"] == run["id"]
    assert snapshot(planner.project) == before


def test_replan_preserves_but_rejects_changed_configuration(replanning):
    planner, _, workflow, run = replanning
    path = planner.project / "harness-project.json"
    config = copy.deepcopy(run["config"])
    config["model"] = "different-model"
    path.write_text(json.dumps(config), encoding="utf-8")
    before = snapshot(planner.project)
    with pytest.raises(HarnessError, match="configuration changed"):
        planner.replan()
    assert snapshot(planner.project) == before
    assert workflow.get() == run


def test_replan_rejects_inputs_changed_during_baseline_collection(replanning, monkeypatch):
    planner, _, workflow, run = replanning
    from development_harness import planning
    original = planning.content_baseline

    def race(project):
        (project / "value.py").write_text("VALUE = 99\n", encoding="utf-8")
        return original(project)

    monkeypatch.setattr(planning, "content_baseline", race)
    with pytest.raises(HarnessError, match="Inputs changed"):
        planner.replan()
    assert (planner.project / "value.py").read_text() == "VALUE = 99\n"
    assert workflow.get() == run


@pytest.mark.parametrize("failure", ["insert_run", "old_event", "new_event"])
def test_replanning_transaction_rolls_back_both_runs_and_both_events(replanning, failure):
    planner, source, workflow, run = replanning
    statements = {
        "insert_run": "CREATE TRIGGER fail_replan BEFORE INSERT ON runs BEGIN SELECT RAISE(ABORT, 'injected replan failure'); END",
        "old_event": "CREATE TRIGGER fail_replan BEFORE INSERT ON events WHEN NEW.kind='workflow_superseded' BEGIN SELECT RAISE(ABORT, 'injected replan failure'); END",
        "new_event": "CREATE TRIGGER fail_replan BEFORE INSERT ON events WHEN NEW.kind='replanning_registered' BEGIN SELECT RAISE(ABORT, 'injected replan failure'); END",
    }
    with planner.store.connect() as db:
        db.execute(statements[failure])
    before = planner.store.events(run["id"])
    with pytest.raises(sqlite3.IntegrityError, match="injected replan failure"):
        planner.replan()
    assert workflow.get() == run
    assert planner.store.active()["id"] == run["id"]
    assert planner.store.latest("planning") == source
    assert planner.store.events(run["id"]) == before


def test_actual_controller_exit_inside_replanning_transaction_preserves_old_owner(replanning):
    planner, source, workflow, run = replanning
    script = '''
from contextlib import contextmanager
import os,sys
from development_harness.planning import Planning
planner=Planning(sys.argv[1],sys.argv[2])
connect=planner.store.connect
@contextmanager
def interrupted():
    with connect() as db:
        class Proxy:
            def execute(self,sql,*args):
                result=db.execute(sql,*args)
                if sql.startswith('INSERT INTO runs'):
                    os._exit(77)
                return result
        yield Proxy()
planner.store.connect=interrupted
planner.replan()
'''
    before = planner.store.events(run["id"])
    result = subprocess.run([sys.executable, "-c", script, str(planner.project), str(planner.store.home)],
                            capture_output=True, timeout=15, creationflags=subprocess.CREATE_NO_WINDOW)
    assert result.returncode == 77, result.stdout + result.stderr
    assert workflow.get() == run
    assert planner.store.active()["id"] == run["id"]
    assert planner.store.latest("planning") == source
    assert planner.store.events(run["id"]) == before
    assert planner.replan()["stage"] == "baseline_pending"


def test_superseded_history_remains_inactive_when_saved_or_transitioned(replanning):
    planner, _, workflow, _ = replanning
    replacement = planner.replan()
    old = workflow.get()
    planner.store.save(old, "historical_result_exported")
    planner.store.transition(old["id"], "historical-note", "historical_note", {},
                             lambda current: current.update(report_note="Preserved history"))
    assert planner.store.active()["id"] == replacement["id"]


def test_replan_rejects_corrupted_replacement_link_without_creating_another_run(replanning):
    planner, _, workflow, _ = replanning
    replacement = planner.replan()
    old = workflow.get()
    old["replanning"]["feedback_ids"] = ["other-feedback"]
    planner.store.save(old, "test_invalid_link")
    with pytest.raises(HarnessError, match="linkage is invalid"):
        planner.replan()
    assert planner.store.latest("planning")["id"] == replacement["id"]


def test_store_replanning_replay_is_stable_and_rejects_changed_evidence(replanning):
    planner, _, _, original = replanning
    replacement = planner.replan()
    events = planner.store.events(original["id"])
    event = events[-1]
    repeated = planner.store.supersede_and_create(original["id"], event["id"], event["kind"], event["data"],
                                                 replacement, lambda _: pytest.fail("Replay changed the old run"))
    assert repeated == replacement
    assert planner.store.events(original["id"]) == events
    changed = event["data"] | {"input_hash": "other-input"}
    with pytest.raises(HarnessError, match="different evidence"):
        planner.store.supersede_and_create(original["id"], event["id"], event["kind"], changed, replacement, lambda _: None)
    assert planner.store.active()["id"] == replacement["id"]


def test_replan_cannot_replace_another_active_owner(replanning):
    planner, source, workflow, original = replanning
    with planner.store.connect() as db:
        db.execute("UPDATE runs SET active=0 WHERE id=?", (original["id"],))
    other = copy.deepcopy(source)
    other.update(id="other-planning-owner", stage="baseline_pending", approval=None)
    planner.store.save(other, "test_other_owner", new=True)
    with pytest.raises(HarnessError, match="no longer owns"):
        planner.replan()
    assert planner.store.active()["id"] == other["id"]
    assert workflow.get() == original
