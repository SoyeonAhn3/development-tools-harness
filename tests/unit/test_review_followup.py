import copy
import json
import sqlite3

import pytest

from development_harness.model import HarnessError, digest
from development_harness.store import Store
from development_harness.worker_contract import (REVIEWER_FOLLOWUP_SCHEMA, REVIEWER_SCHEMA, TaskScope,
                                                 validate_review)
from development_harness.workers import CodexWorker, REVIEWER_FOLLOWUP_INSTRUCTIONS
from development_harness.workflow_records import WorkflowRecords


def finding(identity="local-finding", **changes):
    return {"id": identity, "requirement_id": "R1", "path": "code.py", "severity": "high", "required": True,
            "evidence": "The negative branch still accepts input.", "recommendation": "Reject negative input.", **changes}


def assessment(identity, status="resolved", **changes):
    return {"finding_id": identity, "status": status,
            "reason": "Checked the negative branch against R1.",
            "evidence": "The current guard and negative-input regression assertion reject negative input.", **changes}


def response(prior, status="resolved", **changes):
    repeated = [finding(item["id"]) for item in prior] if status in {"open", "deferred"} else []
    return {"task_id": "T1", "verdict": "changes" if repeated else "pass", "summary": "Independent follow-up",
            "findings": repeated, "questions": [],
            "assessments": [assessment(item["id"], status) for item in prior], **changes}


@pytest.fixture
def context(tmp_path):
    project = tmp_path / "project"
    project.mkdir()
    (project / "code.py").write_text("def accept(value):\n    return value >= 0\n", encoding="utf-8")
    scope = TaskScope(project, "T1", {"R1": "Reject negative input."}, ["code.py"], [])
    prior = [{**finding("finding-controller"), "task_id": "T1", "status": "open"}]
    return scope, prior


@pytest.mark.parametrize("defect", ["omitted", "duplicate", "invented", "empty-reason", "empty-evidence"])
def test_assessments_must_cover_every_supplied_identity_once(context, defect):
    scope, prior = context
    review = response(prior)
    if defect == "omitted":
        review["assessments"] = []
    elif defect == "duplicate":
        review["assessments"] *= 2
    elif defect == "invented":
        review["assessments"][0]["finding_id"] = "invented"
    else:
        review["assessments"][0][defect.removeprefix("empty-")] = " "
    with pytest.raises(HarnessError, match="every prior|reason and concrete"):
        validate_review(review, scope, prior_findings=prior)


@pytest.mark.parametrize("status", ["open", "deferred", "resolved", "false_positive"])
def test_followup_statuses_require_consistent_repeat_identity(context, status):
    scope, prior = context
    review = response(prior, status)
    assert validate_review(review, scope, prior_findings=prior) == review
    review["findings"] = [] if review["findings"] else [finding(prior[0]["id"])]
    with pytest.raises(HarnessError, match="Open/deferred"):
        validate_review(review, scope, prior_findings=prior)


def test_mandatory_deferred_cannot_be_downgraded_to_a_passing_review(context):
    scope, prior = context
    review = response(prior, "deferred", verdict="pass")
    review["findings"][0].update(severity="low", required=False)
    with pytest.raises(HarnessError, match="downgrade"):
        validate_review(review, scope, prior_findings=prior)


def test_developer_claim_does_not_close_a_still_observed_defect(context):
    scope, prior = context
    review = response(prior, findings=[finding(prior[0]["id"])], verdict="changes")
    review["assessments"][0]["evidence"] = "The Developer says fixed."
    with pytest.raises(HarnessError, match="closed findings cannot recur"):
        validate_review(review, scope, prior_findings=prior)


def test_legacy_reviewer_schema_is_unchanged_without_prior_findings(context):
    scope, _ = context
    review = response([])
    review.pop("assessments")
    assert validate_review(review, scope) == review
    assert "assessments" not in REVIEWER_SCHEMA["properties"]
    with pytest.raises(HarnessError, match="unexpected fields"):
        validate_review({**review, "assessments": []}, scope)


def test_worker_pins_followup_input_assessments_and_uses_extended_schema(context, tmp_path, monkeypatch):
    scope, prior = context
    expected = response(prior)
    worker = CodexWorker("reviewer", "local-fixture", tmp_path / "worker")
    worker.policy = {"fixture": True}
    seen = []

    def generate(prompt, schema, attempt, launched, timeout):
        assert REVIEWER_FOLLOWUP_INSTRUCTIONS in prompt
        assert schema == REVIEWER_FOLLOWUP_SCHEMA
        attempt["log"] = str(worker.directory / "events.jsonl")
        (worker.directory / "events.jsonl").write_text(json.dumps({"type": "thread.started", "thread_id": "review"}))
        return expected

    monkeypatch.setattr(worker, "generate", generate)
    result = worker.invoke(scope, before=scope.files, prior_findings=prior,
        validation=[{"id": "check", "content_version": digest(scope.baseline), "outcome": "passed"}],
        lifecycle=lambda attempt, phase: seen.append((phase, copy.deepcopy(attempt))))
    attempt = result["attempt"]
    packet = json.loads((worker.directory / "input.json").read_text())
    assert packet["prior_findings"] == prior
    assert attempt["input_hash"] == digest(packet)
    assert attempt["review_prior_findings"] == prior
    assert attempt["review_prior_findings_hash"] == digest(prior)
    assert attempt["review_assessments_hash"] == digest(expected["assessments"])
    assert seen[0][1]["review_prior_findings_hash"] == digest(prior)
    assert seen[-1][1]["review_assessments_hash"] == digest(expected["assessments"])


@pytest.fixture
def records(context, tmp_path):
    scope, _ = context
    store = Store(scope.project, tmp_path / "runtime")
    policy = {"validation": [{"argv": ["python", "check.py"], "kind": "command", "timeout": 10}]}
    store.save({"id": "workflow", "kind": "workflow", "stage": "workflow_ready",
                "plan_hash": "plan", "policy_hash": digest(policy), "policy": policy, "expected": scope.baseline,
                "attempts": [], "waits": [], "findings": {},
                "tasks": [{"id": "T1", "requirements": ["R1"], "paths": ["code.py"]}]}, "created", new=True)
    return WorkflowRecords(store, "workflow")


def journal_review(records, review, name, prior=None, validation_ids=()):
    run = records.store.get(records.run_id)
    attempt = records.prepare_attempt("T1", "reviewer", digest(run["expected"]), attempt_id=name)
    if prior:
        attempt.update(review_prior_findings=copy.deepcopy(prior), review_prior_findings_hash=digest(prior))
    for phase in ("prepared", "process_registered", "dispatch_intent", "responded", "finished"):
        if phase == "responded":
            attempt.update(response_hash=digest(review), outcome="responded", dispatch_status="responded", confirmed_ai_calls=1)
        if phase == "finished":
            attempt.update(outcome="validated", review_verdict=review["verdict"], review_findings_hash=digest(review["findings"]),
                           review_validation_ids=list(validation_ids))
            if "assessments" in review:
                attempt["review_assessments_hash"] = digest(review["assessments"])
        records.lifecycle(attempt, phase)
    return attempt


def seed(records, count=1):
    findings = [finding("local-" + str(index), evidence="Observed defect " + str(index)) for index in range(count)]
    initial = {"task_id": "T1", "verdict": "changes", "summary": "Needs correction", "findings": findings, "questions": []}
    journal_review(records, initial, "initial")
    return records.ingest_findings("initial", findings)


def journal_validation(records, name="validation", outcome="passed", check_hash=None):
    run = records.store.get(records.run_id)
    attempt = records.prepare_attempt("T1", "validation", digest(run["expected"]), attempt_id=name)
    attempt.update(outcome=outcome, check_hash=check_hash or digest(run["policy"]["validation"][0]))
    records.lifecycle(attempt, "finished")
    return name


@pytest.mark.parametrize("status", ["open", "deferred"])
def test_changed_repeat_wording_keeps_controller_identity_and_mandatory_status(records, status):
    prior = seed(records)
    review = response(prior, status)
    review["findings"][0]["evidence"] = "The rewritten branch continues to accept negative values."
    journal_review(records, review, "followup", prior)
    result = records.apply_review_assessments("followup", review)
    assert len(result) == 1 and result[0]["id"] == prior[0]["id"]
    assert result[0]["status"] == status and result[0]["required"]
    assert records.summary()["blocking_findings"] == [prior[0]["id"]]
    assert [item["kind"] for item in result[0]["history"]] == ["observed", "observed", "disposition"]
    assert records.apply_review_assessments("followup", copy.deepcopy(review)) == result


@pytest.mark.parametrize("status", ["resolved", "false_positive"])
def test_closure_preserves_exact_independent_assessment_evidence(records, status):
    prior = seed(records)
    check = journal_validation(records)
    review = response(prior, status)
    journal_review(records, review, "followup", prior, [check])
    result = records.apply_review_assessments("followup", review)[0]
    assert result["status"] == status
    assert result["history"][-1]["evidence"]["reviewer_evidence"] == review["assessments"][0]["evidence"]
    assert result["history"][-1]["evidence"]["assessment_hash"] == digest(review["assessments"][0])
    assert not records.summary()["blocking_findings"]


@pytest.mark.parametrize("failure", ["failed", "stale", "old-validation", "missing-check", "omitted-assessment", "changed-response"])
def test_unverified_resolution_rolls_back_findings_and_dispositions(records, failure):
    old = journal_validation(records, name="old") if failure == "old-validation" else None
    prior = seed(records)
    check = old or journal_validation(records, outcome="failed" if failure == "failed" else "passed",
                                      check_hash="unapproved" if failure == "missing-check" else None)
    review = response(prior)
    if failure == "omitted-assessment":
        review["assessments"] = []
    journal_review(records, review, "followup", prior, [check])
    if failure == "stale":
        records.store.transition(records.run_id, "code-change", "changed", {}, lambda run: run["expected"].update({"code.py": "later-code"}))
    if failure == "changed-response":
        review["assessments"][0]["reason"] = "Different from observed response"
    before = records.store.get(records.run_id)
    with pytest.raises(HarnessError, match="validation|current code|every prior"):
        records.apply_review_assessments("followup", review)
    assert records.store.get(records.run_id) == before


def test_incomplete_prior_packet_cannot_silently_omit_an_unresolved_finding(records):
    prior = seed(records, count=2)
    review = response(prior[:1], "false_positive")
    journal_review(records, review, "followup", prior[:1])
    with pytest.raises(HarnessError, match="every unresolved"):
        records.apply_review_assessments("followup", review)
    assert len(records.summary()["blocking_findings"]) == 2


def test_assessment_transaction_and_event_roll_back_together(records):
    prior = seed(records)
    check = journal_validation(records)
    review = response(prior)
    journal_review(records, review, "followup", prior, [check])
    before = records.store.get(records.run_id)
    with records.store.connect() as db:
        db.executescript("""CREATE TRIGGER fail_assessment BEFORE INSERT ON events
            WHEN NEW.kind = 'workflow_review_assessed'
            BEGIN SELECT RAISE(ABORT, 'injected review interruption'); END;""")
    with pytest.raises(sqlite3.IntegrityError, match="injected review"):
        records.apply_review_assessments("followup", review)
    assert records.store.get(records.run_id) == before


def test_prior_packet_cannot_be_rewritten_after_prepared_journal_entry(records):
    prior = seed(records)
    run = records.store.get(records.run_id)
    attempt = records.prepare_attempt("T1", "reviewer", digest(run["expected"]), attempt_id="followup")
    attempt.update(review_prior_findings=prior, review_prior_findings_hash=digest(prior))
    records.lifecycle(attempt, "prepared")
    attempt["review_prior_findings"][0]["required"] = False
    with pytest.raises(HarnessError, match="recorded observation cannot change"):
        records.lifecycle(attempt, "process_registered")


def test_out_of_order_open_assessment_cannot_override_a_later_observation(records):
    prior = [{key: value for key, value in item.items() if key != "history"} for item in seed(records)]
    review = response(prior, "open")
    journal_review(records, review, "older-followup", prior)
    # A separate controller observation supersedes the already completed review.
    newer = {"task_id": "T1", "verdict": "changes", "summary": "Observed again",
             "findings": [finding("new-local", evidence=prior[0]["evidence"])], "questions": []}
    journal_review(records, newer, "newer-review")
    records.ingest_findings("newer-review", newer["findings"], mapping={"new-local": prior[0]["id"]})
    # Use the exact unchanged descriptive snapshot normally supplied by the scheduler.
    with pytest.raises(HarnessError, match="after the latest"):
        records.apply_review_assessments("older-followup", review)
