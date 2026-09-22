"""Final evidence gates using actual isolated pytest and local role subprocesses.

No AI service is called. Reuse/manual confirmation and acceptance must never
dispatch a role or start another test command merely to record user decisions.
"""

import copy
import json
from pathlib import Path

import pytest

from development_harness.files import snapshot
from development_harness.model import HarnessError, digest
from development_harness.planning import Planning
from development_harness.workflow import Workflow
from test_workflow import FIRST, admitted_factory, developer, isolated_factory, reviewer, scripted_workers
from test_workflow_admission_cli import call


MANUAL = [{"id": "inspect-source", "requirement_ids": ["R1"],
           "procedure": "Inspect the delivered final value.py source.", "expected": "A is 1 and B is 0."}]
FINAL_TESTS = "from value import A, B\ndef test_final_values():\n    assert A == 1\n    assert B == 0\n"


@pytest.fixture
def completed_factory(admitted_factory, isolated_factory, tmp_path):
    def create(*, reuse=False, manual=False):
        workflow = admitted_factory(tasks=1)
        if reuse or manual:
            workflow.cancel()
            planner = Planning(workflow.project, workflow.store.home)
            if reuse:
                plan = copy.deepcopy(planner.get()["versions"][-1]["plan"])
                words = {"en": "Preserve the required A value in the final code", "ko": "최종 코드에서 요구한 A 값을 유지한다"}
                plan["requirements"].append({"id": "R2", "text": words, "source_quote": "while preserving A.",
                                              "disposition": "reuse", "phase_id": "P1", "verification": words,
                                              "rationale": words})
                path = tmp_path / (workflow.get()["id"] + "-revised.json")
                path.write_text(json.dumps(plan, ensure_ascii=False), encoding="utf-8")
                planner.revise(path)
                planner.approve()
            workflow.prepare(manual_checks=MANUAL if manual else [])
            workflow.approve()
        worker = scripted_workers([developer(files={"value.py": FIRST, "test_value.py": FINAL_TESTS}), reviewer()])
        run = workflow.execute(worker_factory=worker, validator_factory=isolated_factory)
        assert run["stage"] == "technically_complete", run.get("reason")
        assert run["policy"]["result_version"] == 1
        final = next(a for a in run["attempts"] if a["id"] == run["execution"]["final_validation_ids"][0])
        assert final["outcome"] == "passed" and final["tests"] == 1
        assert {"record", "junit"} <= final["artifact_hashes"].keys()
        assert len(worker.calls) == 2 and not worker.pending
        return workflow, worker
    return create


def final_attempt(run):
    return next(a for a in run["attempts"] if a["id"] == run["execution"]["final_validation_ids"][0])


def prohibit_dispatch(monkeypatch):
    monkeypatch.setattr("development_harness.workers.CodexWorker.invoke",
                        lambda *a, **kw: pytest.fail("Evidence/acceptance dispatched an AI role"))
    monkeypatch.setattr("development_harness.isolated_validation.IsolatedValidator.run",
                        lambda *a, **kw: pytest.fail("Evidence/acceptance dispatched a new validation"))


def test_acceptance_is_explicit_idempotent_version_bound_and_releases_ownership(completed_factory, monkeypatch):
    workflow, worker = completed_factory()
    completed = workflow.get()
    planner = Planning(workflow.project, workflow.store.home)
    assert workflow.store.active()["id"] == completed["id"]
    assert workflow.acceptance_status()["ready"]
    assert not workflow.acceptance_status()["accepted"]
    with pytest.raises(HarnessError, match="unfinished run"):
        planner.register(completed["config"])
    before = snapshot(workflow.project)
    prohibit_dispatch(monkeypatch)
    accepted = workflow.accept()
    assert accepted["stage"] == "accepted" and workflow.store.active() is None
    assert accepted["approval"] == completed["approval"]
    assert accepted["acceptance"]["scope"] == "result_acceptance"
    for key in ("plan_hash", "policy_hash", "content_version"):
        assert accepted["acceptance"][key] == completed[key]
    assert accepted["acceptance"]["validation_ids"] == completed["execution"]["final_validation_ids"]
    events = workflow.store.events(accepted["id"])
    assert workflow.accept() == accepted
    assert workflow.store.events(accepted["id"]) == events
    assert workflow.acceptance_status()["accepted"]
    assert snapshot(workflow.project) == before and len(worker.calls) == 2
    next_plan = planner.register(completed["config"])
    assert next_plan["kind"] == "planning" and next_plan["approval"] is None
    assert planner.store.active()["id"] == next_plan["id"]


def test_acceptance_before_execution_cannot_dispatch_or_approve(admitted_factory, monkeypatch):
    workflow = admitted_factory(tasks=1)
    before = workflow.get()
    prohibit_dispatch(monkeypatch)
    with pytest.raises(HarnessError, match="Technical completion"):
        workflow.accept()
    assert workflow.get() == before
    assert not workflow.acceptance_status()["ready"]


def test_user_edits_after_completion_are_preserved_and_block_acceptance(completed_factory):
    workflow, _ = completed_factory()
    run = workflow.get()
    path = workflow.project / "value.py"
    path.write_text("A = 99\nB = 0\n# User edit must survive.\n", encoding="utf-8")
    before = snapshot(workflow.project)
    with pytest.raises(HarnessError, match="acceptance blocked"):
        workflow.accept()
    assert snapshot(workflow.project) == before
    assert workflow.get() == run
    assert not workflow.acceptance_status()["ready"]


def test_edit_during_final_evidence_inspection_blocks_acceptance(completed_factory, monkeypatch):
    import development_harness.workflow_acceptance as acceptance

    workflow, _ = completed_factory()
    run = workflow.get()
    events = workflow.store.events(run["id"])
    inspect_artifacts = acceptance._artifacts
    path = workflow.project / "value.py"
    edited = "A = 99\nB = 0\n# Editor changed this during final evidence inspection.\n"

    def inspect_then_edit(item, required_seals):
        inspect_artifacts(item, required_seals)
        path.write_text(edited, encoding="utf-8")

    monkeypatch.setattr(acceptance, "_artifacts", inspect_then_edit)
    prohibit_dispatch(monkeypatch)
    with pytest.raises(HarnessError, match="acceptance blocked"):
        workflow.accept()
    assert path.read_text(encoding="utf-8") == edited
    assert workflow.get() == run
    assert workflow.store.events(run["id"]) == events
    assert workflow.store.active()["id"] == run["id"]


def test_legacy_policy_cannot_silently_gain_result_acceptance(admitted_factory):
    workflow = admitted_factory(tasks=1)
    run = workflow.get()
    # A historical completion label cannot supply the missing approval policy.
    # Rejection must specifically identify legacy policy before trusting it.
    run["stage"] = "technically_complete"
    run["policy"].pop("result_version")
    run["policy_hash"] = digest(run["policy"])
    run["approval"]["policy_hash"] = run["policy_hash"]
    workflow.store.save(run, "test_legacy_execution_policy")
    before = workflow.store.events(run["id"])
    with pytest.raises(HarnessError, match="acceptance blocked"):
        workflow.accept()
    gate = workflow.acceptance_status()
    assert not gate["ready"] and not gate["technical_ready"]
    assert any("policy" in message.lower() for message in gate["blockers"])
    assert workflow.get() == run
    assert workflow.store.events(run["id"]) == before


@pytest.mark.parametrize("artifact,damage", [("record", "missing"), ("record", "changed"),
                                            ("junit", "missing"), ("junit", "changed"), ("log", "changed")])
def test_missing_or_changed_actual_final_artifact_blocks_acceptance(completed_factory, artifact, damage):
    workflow, _ = completed_factory()
    run = workflow.get()
    evidence = final_attempt(run)
    path = Path(evidence[artifact])
    if damage == "missing":
        path.unlink()
    else:
        path.write_bytes(path.read_bytes() + b"\nchanged after validation\n")
    before = workflow.store.events(run["id"])
    with pytest.raises(HarnessError, match="acceptance blocked"):
        workflow.accept()
    assert workflow.get() == run
    assert workflow.store.events(run["id"]) == before


@pytest.mark.parametrize("damage", ["missing", "changed"])
def test_missing_or_modified_independent_review_response_blocks_acceptance(completed_factory, damage):
    workflow, _ = completed_factory()
    run = workflow.get()
    reviewer_id = run["execution"]["task_states"]["T1"]["reviewer_attempt_id"]
    path = workflow.store.directory / "workflow" / run["id"] / reviewer_id / "response.json"
    if damage == "missing":
        path.unlink()
    else:
        response = json.loads(path.read_text(encoding="utf-8"))
        response["summary"] = "An altered response is not the reviewed evidence."
        path.write_text(json.dumps(response), encoding="utf-8")
    with pytest.raises(HarnessError, match="acceptance blocked"):
        workflow.accept()
    assert workflow.get() == run


@pytest.mark.parametrize("damage", ["missing_id", "failed", "stale_content", "missing_seal", "earlier_task_batch"])
def test_unverified_final_batch_cannot_be_accepted(completed_factory, damage):
    workflow, _ = completed_factory()
    run = workflow.get()
    evidence = final_attempt(run)
    if damage == "missing_id":
        run["execution"]["final_validation_ids"] = ["unknown-check"]
    elif damage == "failed":
        evidence["outcome"] = "failed"
    elif damage == "stale_content":
        evidence["content_version"] = run["initial_content_version"]
    elif damage == "missing_seal":
        evidence["artifact_hashes"].pop("record")
    else:
        earlier = next(a for a in run["attempts"] if a["role"] == "validation" and a["id"] != evidence["id"])
        assert earlier["content_version"] == run["content_version"]
        run["execution"]["final_validation_ids"] = [earlier["id"]]
    workflow.store.save(run, "test_invalid_final_evidence")
    with pytest.raises(HarnessError, match="acceptance blocked"):
        workflow.accept()
    assert workflow.get()["stage"] == "technically_complete"


def test_unresolved_mandatory_finding_blocks_even_with_all_final_checks_passing(completed_factory):
    workflow, _ = completed_factory()
    run = workflow.get()
    run["findings"]["unresolved"] = {"id": "unresolved", "task_id": "T1", "required": True,
                                       "status": "deferred", "history": [], "requirement_id": "R1"}
    workflow.store.save(run, "test_mandatory_deferred_finding")
    with pytest.raises(HarnessError, match="Mandatory review findings"):
        workflow.accept()
    assert not workflow.acceptance_status()["ready"]


def test_reuse_without_task_requires_actual_final_evidence_and_preserves_failed_history(completed_factory, monkeypatch):
    workflow, worker = completed_factory(reuse=True)
    run = workflow.get()
    assert all("R2" not in task["requirements"] for task in run["tasks"])
    gate = workflow.acceptance_status()
    assert gate["technical_ready"] and gate["reuse"][0]["status"] == "missing" and not gate["ready"]
    with pytest.raises(HarnessError, match="Reuse requirement R2"):
        workflow.accept()
    source = workflow.store.get(run["planning_run_id"])
    baseline = source["baseline_evidence"][0]["id"]
    with pytest.raises(HarnessError, match="actual passing final"):
        workflow.record_reuse("R2", [baseline], "The old baseline is not final evidence.")
    ids = run["execution"]["final_validation_ids"]
    prohibit_dispatch(monkeypatch)
    workflow.record_reuse("R2", ids, "The final requirement has not been confirmed.", outcome="failed", record_id="reuse-failed")
    assert workflow.acceptance_status()["reuse"][0]["status"] == "failed"
    with pytest.raises(HarnessError, match="Reuse requirement R2 is failed"):
        workflow.accept()
    workflow.record_reuse("R2", ids, "Final test_final_values asserts the preserved A value is 1.", record_id="reuse-passed")
    after = workflow.get()
    assert [r["outcome"] for r in after["reuse_evidence"]] == ["failed", "passed"]
    assert all(r["content_version"] == after["content_version"] and r["plan_hash"] == after["plan_hash"]
               for r in after["reuse_evidence"])
    events = workflow.store.events(run["id"])
    workflow.record_reuse("R2", ids, "Final test_final_values asserts the preserved A value is 1.", record_id="reuse-passed")
    assert workflow.store.events(run["id"]) == events
    assert workflow.accept()["stage"] == "accepted" and len(worker.calls) == 2


def test_stale_reuse_confirmation_is_not_accepted(completed_factory):
    workflow, _ = completed_factory(reuse=True)
    run = workflow.get()
    workflow.record_reuse("R2", run["execution"]["final_validation_ids"], "Confirmed against the actual final test.")
    changed = workflow.get()
    changed["reuse_evidence"][-1]["content_version"] = changed["initial_content_version"]
    workflow.store.save(changed, "test_stale_reuse_confirmation")
    assert workflow.acceptance_status()["reuse"][0]["status"] == "stale"
    with pytest.raises(HarnessError, match="Reuse requirement R2 is stale"):
        workflow.accept()


def test_pinned_manual_checks_require_current_passing_confirmation(completed_factory, monkeypatch):
    workflow, worker = completed_factory(manual=True)
    run = workflow.get()
    assert run["policy"]["manual_checks"] == MANUAL
    assert workflow.acceptance_status()["manual"][0]["status"] == "missing"
    prohibit_dispatch(monkeypatch)
    with pytest.raises(HarnessError, match="Manual check"):
        workflow.accept()
    with pytest.raises(HarnessError, match="pinned before"):
        workflow.record_manual("unknown", "passed", "Not an approved required check.")
    with pytest.raises(HarnessError, match="pinned"):
        workflow.prepare(manual_checks=[])
    workflow.record_manual("inspect-source", "failed", "The expected source result was not confirmed.", record_id="manual-failed")
    assert workflow.acceptance_status()["manual"][0]["status"] == "failed"
    with pytest.raises(HarnessError, match="Manual check inspect-source is failed"):
        workflow.accept()
    workflow.record_manual("inspect-source", "passed", "Inspected final value.py: A = 1 and B = 0.", record_id="manual-first")
    stale = workflow.get()
    stale["manual_checks"][-1]["completion_id"] = "older-completion"
    workflow.store.save(stale, "test_stale_manual_confirmation")
    assert workflow.acceptance_status()["manual"][0]["status"] == "stale"
    with pytest.raises(HarnessError, match="Manual check inspect-source is stale"):
        workflow.accept()
    workflow.record_manual("inspect-source", "passed", "Repeated the inspection against this final result.", record_id="manual-current")
    assert workflow.acceptance_status()["ready"]
    accepted = workflow.accept()
    assert accepted["acceptance"]["manual_check_ids"] == ["manual-current"]
    assert [r["outcome"] for r in accepted["manual_checks"]] == ["failed", "passed", "passed"]
    assert len(worker.calls) == 2


def test_cli_final_reuse_manual_and_acceptance_preserve_evidence_without_dispatch(completed_factory, tmp_path):
    workflow, worker = completed_factory(reuse=True, manual=True)
    run = workflow.get()
    baseline_attempts = copy.deepcopy(run["attempts"])
    refused = call(workflow, "workflow-accept", expected=2)
    assert "acceptance blocked" in refused["error"]
    final_id = run["execution"]["final_validation_ids"][0]
    note = tmp_path / "manual-observation.txt"
    note.write_text("Inspected final delivered source: A = 1, B = 0.\n", encoding="utf-8")
    call(workflow, "workflow-reuse", "--requirement", "R2", "--validation-ids", final_id,
         "--outcome", "passed", "--record-id", "cli-reuse", "--evidence", "Final test_final_values confirms A remains 1.")
    call(workflow, "workflow-manual", "--check", "inspect-source", "--outcome", "passed",
         "--record-id", "cli-manual", "--evidence-file", str(note))
    call(workflow, "workflow-accept")
    accepted = workflow.get()
    assert accepted["stage"] == "accepted" and accepted["attempts"] == baseline_attempts
    assert accepted["manual_checks"][-1]["evidence"] == note.read_text(encoding="utf-8")
    events = workflow.store.events(run["id"])
    call(workflow, "workflow-accept")
    assert workflow.store.events(run["id"]) == events
    assert len(worker.calls) == 2
