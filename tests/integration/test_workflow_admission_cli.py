"""Run admission commands in actual CLI processes, without AI service calls."""

import json
import os
from pathlib import Path
import subprocess
import sys
import time

import pytest

from development_harness.files import snapshot
from development_harness.planning import Planning


def call(planner, *args, expected=0):
    environment = os.environ.copy()
    environment["DEVELOPMENT_HARNESS_CODEX_PATH"] = str(planner.store.home / "must-not-launch.exe")
    result = subprocess.run(
        [sys.executable, "-m", "development_harness", "--project", str(planner.project),
         "--state-dir", str(planner.store.home), *args],
        capture_output=True, text=True, timeout=30, env=environment,
    )
    assert result.returncode == expected, result.stdout + result.stderr
    return json.loads(result.stdout if result.stdout else result.stderr)


@pytest.fixture
def reviewed_planning(tmp_path):
    project = tmp_path / "CLI workflow 한글"
    project.mkdir()
    (project / "spec.md").write_text("Reject negative values.\n", encoding="utf-8")
    (project / "value.py").write_text("VALUE = 1\n", encoding="utf-8")
    (project / "test_value.py").write_text("from value import VALUE\ndef test_value():\n    assert VALUE == 1\n")
    words = {"en": "Validate negative values", "ko": "음수를 검증한다"}
    plan = {
        "overview": words, "technology": {"en": "Python and pytest", "ko": "Python과 pytest"},
        "current_phase": "P1",
        "phases": [{"id": "P1", "title": words, "goal": words, "exit_criteria": words}],
        "tasks": [{"id": "T1", "title": words, "requirements": ["R1"], "paths": ["value.py"],
                   "acceptance": words, "verification": words, "depends_on": []}],
        "requirements": [{"id": "R1", "text": words, "source_quote": "Reject negative values.",
                          "disposition": "implement", "phase_id": "P1", "verification": words, "rationale": words}],
        "code_context": [{"path": "value.py", "summary": words, "evidence": "VALUE = 1", "kind": "explicit"}],
        "questions": [],
    }

    class FixtureAdapter:
        """Only planning preparation is injected; all admission CLI calls are real."""
        def __init__(self, model, directory):
            Path(directory).mkdir(parents=True, exist_ok=True)

        def verify(self):
            return {"boundary": "local planning fixture, no AI service"}

        def generate(self, prompt, schema, attempt, launched, timeout):
            attempt.update(outcome="running")
            launched(attempt)
            attempt.update(ended=time.time(), duration=0.0, outcome="responded")
            return plan

    planner = Planning(project, tmp_path / "state")
    planner.register({"version": 1, "spec": "spec.md", "context": ["value.py"], "model": "test-model",
                      "planner_timeout": 30, "validation": [
                          {"argv": ["{python}", "-m", "pytest", "-q"], "kind": "pytest", "timeout": 15}]})
    result = planner.plan(adapter_factory=FixtureAdapter)
    assert result["stage"] == "awaiting_plan_approval", result.get("reason")
    return planner


@pytest.mark.parametrize("explicit_source", [False, True])
def test_cli_prepare_status_approve_cancel_preserve_planning_and_project(reviewed_planning, explicit_source):
    planner = reviewed_planning
    planning = call(planner, "plan-approve")
    before = snapshot(planner.project)
    arguments = ["workflow-prepare"] + (["--planning-run", planning["id"]] if explicit_source else [])
    prepared = call(planner, *arguments)
    assert prepared["stage"] == "awaiting_execution_approval"
    assert prepared["execution_authorized"] is False
    assert prepared["workflow_execution_enabled"] is True
    assert prepared["orchestration_available"] is True
    assert prepared["attempts"] == []
    assert isinstance(prepared["findings"], dict)
    assert call(planner, *arguments)["id"] == prepared["id"]
    assert call(planner, "workflow-status")["id"] == prepared["id"]
    assert call(planner, "plan-status")["id"] == planning["id"]
    assert call(planner, "plan-approve")["approval"] == planning["approval"]
    approved = call(planner, "workflow-approve")
    assert approved["stage"] == "execution_ready"
    assert approved["approval"]["scope"] == "execution"
    assert approved["execution_authorized"] is True
    assert call(planner, "workflow-approve")["approval"] == approved["approval"]
    assert approved["attempts"] == []
    assert approved["workflow_execution_enabled"] is True
    for command in ("run", "resume", "accept"):
        assert "workflow" in call(planner, command, expected=2)["error"]
    cancelled = call(planner, "workflow-cancel")
    assert cancelled["stage"] == "cancelled"
    assert call(planner, "workflow-cancel")["id"] == cancelled["id"]
    assert call(planner, "workflow-status")["attempts"] == []
    assert call(planner, "plan-status")["id"] == planning["id"]
    assert planner.store.active() is None
    assert snapshot(planner.project) == before


def test_cli_plan_approval_does_not_imply_execution_authorization(reviewed_planning):
    planner = reviewed_planning
    source = planner.get()
    refused = call(planner, "workflow-prepare", expected=2)
    assert "approved planning" in refused["error"]
    assert planner.store.get()["id"] == source["id"]
    approved = call(planner, "plan-approve")
    assert approved["approval"]["scope"] == "planning_only"
    assert approved["implementation_available"] is False
    assert "planning-only" in call(planner, "run", expected=2)["error"]


def test_cli_changed_code_reports_stale_admission_and_preserves_edit_on_cancel(reviewed_planning):
    planner = reviewed_planning
    call(planner, "plan-approve")
    run = call(planner, "workflow-prepare")
    (planner.project / "value.py").write_text("user edit after preparation\n")
    before = snapshot(planner.project)
    status = call(planner, "workflow-status", expected=1)
    assert status["id"] == run["id"]
    assert "inspection_error" in status
    assert "Unexpected file changes" in call(planner, "workflow-approve", expected=2)["error"]
    cancelled = call(planner, "workflow-cancel", expected=1)
    assert cancelled["stage"] == "cancelled"
    assert cancelled["approval"] is None
    assert snapshot(planner.project) == before


def test_cli_run_observes_policy_approval_and_stops_on_missing_worker(reviewed_planning):
    planner = reviewed_planning
    call(planner, "plan-approve")
    prepared = call(planner, "workflow-prepare", "--max-corrections", "0")
    assert prepared["max_corrections"] == 0
    assert "approval" in call(planner, "workflow-run", expected=2)["error"]
    call(planner, "workflow-approve")
    assert "positive" in call(planner, "workflow-run", "--steps", "0", expected=2)["error"]
    before = snapshot(planner.project)
    stopped = call(planner, "workflow-run", expected=1)
    assert stopped["stage"] == "stopped"
    assert stopped["execution"]["corrections"] == {"T1": 0}
    assert len(stopped["attempts"]) == 1
    assert stopped["attempts"][0]["dispatch_status"] == "not_sent"
    assert stopped["ai_dispatch_attempts"] == 0
    assert call(planner, "workflow-run", expected=1) == stopped
    assert snapshot(planner.project) == before
