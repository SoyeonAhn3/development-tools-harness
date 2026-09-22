import copy
import sqlite3

import pytest

from development_harness.model import HarnessError, digest
from development_harness.store import Store
from development_harness.workflow_records import WorkflowRecords


@pytest.fixture
def records(tmp_path):
    project = tmp_path / "project"
    project.mkdir()
    store = Store(project, tmp_path / "runtime")
    checks = [{"argv": ["python", "check.py"], "kind": "command", "timeout": 10}]
    policy = {"validation": checks}
    store.save({"id": "workflow", "kind": "workflow", "stage": "workflow_ready",
                "plan_hash": "plan-v1", "policy_hash": digest(policy), "policy": policy,
                "expected": {"code.py": "original-code"}, "attempts": [], "waits": [], "findings": {},
                "tasks": [{"id": "T1", "requirements": ["R1"], "paths": ["code.py"]},
                          {"id": "T2", "requirements": ["R2"], "paths": ["other.py"]}]},
               "created", new=True)
    return WorkflowRecords(store, "workflow")


def prepared(records, role="developer", name="attempt", task="T1"):
    version = digest(records.store.get(records.run_id)["expected"])
    return records.prepare_attempt(task, role, version, attempt_id=name)


def observe(records, attempt, phase, **changes):
    if phase == "responded":
        attempt.update(response_hash=digest({"fixture_response_for": attempt["id"]}),
                       dispatch_status="responded", confirmed_ai_calls=1)
    attempt.update(changes)
    attempt[phase + "_at"] = {"prepared": 10, "process_registered": 11, "dispatch_intent": 12,
                              "responded": 14, "finished": 15}[phase]
    return records.lifecycle(attempt, phase)


def reviewer(records, findings, name="review", verdict=None):
    attempt = prepared(records, "reviewer", name)
    observe(records, attempt, "prepared", input_hash="packet")
    observe(records, attempt, "process_registered", started=11, process={"pid": 123})
    observe(records, attempt, "dispatch_intent", dispatch_status="uncertain")
    observe(records, attempt, "responded", outcome="responded", usage={"input_tokens": 7, "output_tokens": 3})
    observe(records, attempt, "finished", outcome="validated", ended=15, duration=4,
            session_id="session-" + name, review_verdict=verdict or ("changes" if findings else "pass"),
            review_findings_hash=digest(findings), review_validation_ids=[
                item["id"] for item in records.store.get(records.run_id)["attempts"] if item["role"] == "validation"])
    return attempt


def validation(records, name="validation", outcome="passed", check_hash=None):
    attempt = prepared(records, "validation", name)
    if check_hash is None:
        check_hash = digest(records.store.get(records.run_id)["policy"]["validation"][0])
    observe(records, attempt, "finished", outcome=outcome, started=11, ended=12, duration=1,
            check_hash=check_hash, log="validation.log")
    return attempt


def finding(local_id="F1", **changes):
    return {"id": local_id, "requirement_id": "R1", "path": "code.py", "severity": "high", "required": True,
            "evidence": "The negative branch accepts input.", "recommendation": "Reject negative input.", **changes}


def registered_finding(records):
    review = reviewer(records, [finding()])
    return records.ingest_findings(review["id"], [finding()])[0]


def test_prepare_is_durable_replay_safe_and_binds_plan_and_code(records):
    attempt = prepared(records)
    restarted = WorkflowRecords(records.store, records.run_id)
    assert prepared(restarted) == attempt
    assert attempt["plan_hash"] == "plan-v1"
    assert attempt["policy_hash"] == records.store.get(records.run_id)["policy_hash"]
    assert len(records.store.get(records.run_id)["attempts"]) == 1
    assert len(records.store.events(records.run_id)) == 2
    with pytest.raises(HarnessError, match="different evidence"):
        records.prepare_attempt("T1", "developer", "changed-code", attempt_id="attempt")


def test_prepare_rejects_stale_content_or_unknown_task(records):
    with pytest.raises(HarnessError, match="admitted code"):
        records.prepare_attempt("T1", "developer", "stale")
    with pytest.raises(HarnessError, match="outside the approved plan"):
        prepared(records, task="unknown")
    assert records.store.get(records.run_id)["attempts"] == []


def test_attempt_state_and_event_roll_back_together_when_insert_fails(records):
    attempt = prepared(records)
    before = records.store.get(records.run_id)
    with records.store.connect() as db:
        db.executescript("""CREATE TRIGGER fail_event BEFORE INSERT ON events
            WHEN NEW.kind = 'workflow_attempt_prepared'
            BEGIN SELECT RAISE(ABORT, 'injected interruption'); END;""")
    with pytest.raises(sqlite3.IntegrityError, match="injected interruption"):
        observe(records, attempt, "prepared", input_hash="packet")
    assert records.store.get(records.run_id) == before
    assert len(records.store.events(records.run_id)) == 2


def test_process_start_does_not_count_as_ai_call(records):
    attempt = prepared(records)
    observe(records, attempt, "prepared", input_hash="packet")
    observe(records, attempt, "process_registered", started=11, process={"pid": 42})
    result = records.summary()
    assert result["ai_dispatch_attempts"] == result["confirmed_ai_calls"] == result["total_ai_calls"] == 0
    assert result["duration"] is None
    assert result["usage"] is result["cost"] is None


def test_interrupted_dispatch_is_unknown_and_cannot_be_silently_retried(records):
    attempt = prepared(records)
    observe(records, attempt, "prepared", input_hash="packet")
    observe(records, attempt, "process_registered", started=11)
    observe(records, attempt, "dispatch_intent", dispatch_status="uncertain")
    snapshot = copy.deepcopy(attempt)
    records.lifecycle(snapshot, "dispatch_intent")
    observe(records, attempt, "finished", outcome="interrupted", ended=None, duration=None)
    result = records.summary()
    assert result["ai_dispatch_attempts"] == result["uncertain_ai_calls"] == 1
    assert result["confirmed_ai_calls"] == 0
    assert result["total_ai_calls"] is result["duration"] is result["usage"] is None
    with pytest.raises(HarnessError, match="reconciliation"):
        prepared(records, name="retry")
    assert len(records.store.get(records.run_id)["attempts"]) == 1


@pytest.mark.parametrize("field,value", [("role", "reviewer"), ("task_id", "T2"),
                                        ("content_version", "other"), ("plan_hash", "other"),
                                        ("policy_hash", "other")])
def test_callback_rejects_changed_attempt_identity(records, field, value):
    attempt = prepared(records)
    attempt[field] = value
    with pytest.raises(HarnessError, match="identity/version mismatch"):
        observe(records, attempt, "prepared", input_hash="packet")


def test_callback_rejects_changed_bound_input_and_out_of_order_response(records):
    attempt = prepared(records)
    observe(records, attempt, "prepared", input_hash="packet")
    with pytest.raises(HarnessError, match="input hash"):
        observe(records, attempt, "process_registered", input_hash="another packet")
    attempt["input_hash"] = "packet"
    with pytest.raises(HarnessError, match="out of order"):
        observe(records, attempt, "responded")


@pytest.mark.parametrize("field,value", [("process", {"pid": 999}), ("started", 12), ("prepared_at", 99)])
def test_later_callback_cannot_rewrite_observed_process_or_time(records, field, value):
    attempt = prepared(records)
    observe(records, attempt, "prepared")
    observe(records, attempt, "process_registered", started=11, process={"pid": 42})
    attempt[field] = value
    with pytest.raises(HarnessError, match="recorded observation cannot change"):
        observe(records, attempt, "dispatch_intent")
    recorded = records.store.get(records.run_id)["attempts"][0]
    assert recorded["process"] == {"pid": 42} and recorded["started"] == 11 and recorded["prepared_at"] == 10


def test_final_observation_preserves_response_when_responded_transaction_failed(records, monkeypatch):
    attempt = prepared(records)
    observe(records, attempt, "prepared")
    observe(records, attempt, "process_registered", started=11)
    observe(records, attempt, "dispatch_intent", dispatch_status="uncertain")
    transition = records.store.transition
    def fail_response(run_id, event_id, kind, detail, update):
        if kind == "workflow_attempt_responded":
            raise sqlite3.OperationalError("interrupted response commit")
        return transition(run_id, event_id, kind, detail, update)
    monkeypatch.setattr(records.store, "transition", fail_response)
    with pytest.raises(sqlite3.OperationalError, match="interrupted response commit"):
        observe(records, attempt, "responded", outcome="responded", usage={"input_tokens": 7})
    observe(records, attempt, "finished", outcome="unverified", ended=15, duration=4,
            reason="Response callback failed")
    saved = records.store.get(records.run_id)["attempts"][0]
    assert saved["outcome"] == "unverified" and "responded" not in saved["journal_phases"]
    assert records.summary()["confirmed_ai_calls"] == 1
    assert records.summary()["uncertain_ai_calls"] == 0
    assert records.summary()["usage"] == {"input_tokens": 7}


def test_known_duration_must_match_actual_observed_endpoints(records):
    attempt = prepared(records)
    with pytest.raises(HarnessError, match="duration does not match"):
        observe(records, attempt, "finished", started=11, ended=15, duration=999, outcome="unverified")


def test_completed_observations_are_counted_once_and_unknown_usage_is_not_zero(records):
    attempt = reviewer(records, [], name="one")
    records.lifecycle(copy.deepcopy(attempt), "finished")
    second = reviewer(records, [], name="two")
    result = records.summary()
    assert result["attempt_count"] == result["confirmed_ai_calls"] == result["ai_dispatch_attempts"] == 2
    assert result["usage"] == {"input_tokens": 14, "output_tokens": 6}
    # Unknown usage on a separate confirmed call invalidates the total, not the observed count.
    third = prepared(records, "reviewer", "three")
    observe(records, third, "prepared")
    observe(records, third, "process_registered")
    observe(records, third, "dispatch_intent")
    observe(records, third, "responded", usage=None)
    observe(records, third, "finished", outcome="unverified")
    assert records.summary()["usage"] == {"input_tokens": None, "output_tokens": None}
    assert second["session_id"] != attempt["session_id"]


def test_wait_replay_does_not_reset_clock_or_double_count(records, monkeypatch):
    monkeypatch.setattr("development_harness.workflow_records.time.time", lambda: 10)
    initial = records.start_wait("execution_approval", "wait")
    monkeypatch.setattr("development_harness.workflow_records.time.time", lambda: 30)
    assert records.start_wait("execution_approval", "wait") == initial
    assert records.summary()["approval_wait"] is None
    interval = records.finish_wait("wait")
    monkeypatch.setattr("development_harness.workflow_records.time.time", lambda: 100)
    assert records.finish_wait("wait") == interval
    assert records.summary()["approval_wait"] == 20
    with pytest.raises(HarnessError, match="different evidence"):
        records.finish_wait("wait", ended=101)


def test_wait_clock_regression_is_rejected_and_unknown_start_is_preserved(records):
    records.start_wait("approval", "clock", started=20)
    with pytest.raises(HarnessError, match="precedes"):
        records.finish_wait("clock", ended=19)
    assert records.summary()["approval_wait"] is None
    records.store.transition(records.run_id, "import-wait", "imported", {},
        lambda run: run["waits"].append({"id": "unknown-start", "reason": "approval", "started": None, "ended": None, "duration": None}))
    assert records.finish_wait("unknown-start", ended=25)["duration"] is None


def test_findings_have_controller_ids_and_exact_rereview_keeps_identity(records):
    initial = registered_finding(records)
    assert initial["id"] != "F1"
    assert records.ingest_findings("review", [finding()]) == [initial]
    reviewer(records, [finding("local-9")], name="again")
    repeated = records.ingest_findings("again", [finding("local-9")])[0]
    assert repeated["id"] == initial["id"]
    assert len(repeated["history"]) == 2
    assert records.summary()["finding_count"] == 1


def test_explicit_mapping_preserves_id_through_changed_wording(records):
    initial = registered_finding(records)
    revised = finding("new-local", evidence="A changed negative branch still accepts input.")
    reviewer(records, [revised], name="again")
    result = records.ingest_findings("again", [revised], mapping={"new-local": initial["id"]})
    assert result[0]["id"] == initial["id"]
    assert result[0]["evidence"] == revised["evidence"]
    assert records.summary()["finding_count"] == 1


def test_finding_ingest_requires_exact_validated_response(records):
    reviewer(records, [finding()])
    with pytest.raises(HarnessError, match="exact validated"):
        records.ingest_findings("review", [finding(evidence="invented")])
    assert records.summary()["finding_count"] == 0


def test_invalid_mapping_rolls_back_all_finding_changes(records):
    reviewer(records, [finding()])
    with pytest.raises(HarnessError, match="unobserved local"):
        records.ingest_findings("review", [finding()], mapping={"missing": "anything"})
    assert records.store.get(records.run_id)["findings"] == {}


def test_deferred_mandatory_finding_stays_blocking_and_developer_claim_cannot_resolve(records):
    initial = registered_finding(records)
    result = records.set_finding_status(initial["id"], "deferred", evidence={"reason": "Requires later work"})
    assert result["status"] == "deferred"
    assert records.summary()["blocking_findings"] == [initial["id"]]
    with pytest.raises(HarnessError, match="Unknown workflow attempt"):
        records.set_finding_status(initial["id"], "resolved", evidence={"reason": "Developer says fixed"})


def test_resolution_requires_followup_and_all_passing_version_matched_checks(records):
    initial = registered_finding(records)
    check = validation(records)
    reviewer(records, [], name="followup")
    records.ingest_findings("followup", [])
    evidence = {"reason": "Follow-up confirms negative rejection", "reviewer_attempt_id": "followup",
                "validation_attempt_ids": [check["id"]]}
    result = records.set_finding_status(initial["id"], "resolved", evidence=evidence)
    assert result["status"] == "resolved"
    assert records.summary()["blocking_findings"] == []
    assert records.set_finding_status(initial["id"], "resolved", evidence=evidence) == result
    # A later real recurrence reopens the same controller identity.
    reviewer(records, [finding()], name="recurrence")
    assert records.ingest_findings("recurrence", [finding()])[0]["status"] == "open"


@pytest.mark.parametrize("failure", ["failed", "missing-check", "stale", "blocked-review", "still-present"])
def test_resolution_rejects_unverified_or_incomplete_evidence(records, failure):
    initial = registered_finding(records)
    check = validation(records, outcome="failed" if failure == "failed" else "passed",
                       check_hash="unapproved-check" if failure == "missing-check" else None)
    findings = [finding()] if failure == "still-present" else []
    reviewer(records, findings, name="followup", verdict="blocked" if failure == "blocked-review" else None)
    records.ingest_findings("followup", findings)
    if failure == "stale":
        records.store.transition(records.run_id, "change-code", "changed", {},
                                 lambda run: run["expected"].update({"code.py": "new-code"}))
    with pytest.raises(HarnessError, match="Closure|validation"):
        records.set_finding_status(initial["id"], "resolved", evidence={"reason": "Claim", "reviewer_attempt_id": "followup",
                                  "validation_attempt_ids": [check["id"]]})
    assert records.summary()["blocking_findings"] == [initial["id"]]


def test_false_positive_requires_reviewed_evidence(records):
    initial = registered_finding(records)
    with pytest.raises(HarnessError, match="nonempty text"):
        records.set_finding_status(initial["id"], "false_positive", evidence={"reason": ""})
    reviewer(records, [], name="followup")
    records.ingest_findings("followup", [])
    result = records.set_finding_status(initial["id"], "false_positive", evidence={
        "reason": "Follow-up verifies the existing guard already rejects negatives", "reviewer_attempt_id": "followup"})
    assert result["status"] == "false_positive"
    assert not records.summary()["blocking_findings"]


def test_old_clear_review_cannot_close_a_later_finding(records):
    reviewer(records, [], name="old-clear")
    records.ingest_findings("old-clear", [])
    initial = registered_finding(records)
    with pytest.raises(HarnessError, match="after the latest"):
        records.set_finding_status(initial["id"], "false_positive", evidence={
            "reason": "Old review passed", "reviewer_attempt_id": "old-clear"})


def test_resolving_requires_validation_rerun_and_actual_reviewer_input(records):
    validation(records, name="old-tests")
    initial = registered_finding(records)
    reviewer(records, [], name="followup")
    records.ingest_findings("followup", [])
    with pytest.raises(HarnessError, match="validation"):
        records.set_finding_status(initial["id"], "resolved", evidence={"reason": "Old tests passed",
            "reviewer_attempt_id": "followup", "validation_attempt_ids": ["old-tests"]})
    validation(records, name="late-tests")
    with pytest.raises(HarnessError, match="not supplied"):
        records.set_finding_status(initial["id"], "resolved", evidence={"reason": "New tests passed",
            "reviewer_attempt_id": "followup", "validation_attempt_ids": ["late-tests"]})


def test_mandatory_finding_cannot_be_downgraded_by_remapping(records):
    initial = registered_finding(records)
    records.set_finding_status(initial["id"], "deferred", evidence={"reason": "Later work"})
    optional = finding("optional-local", severity="low", required=False)
    reviewer(records, [optional], name="downgrade", verdict="pass")
    repeated = records.ingest_findings("downgrade", [optional], mapping={"optional-local": initial["id"]})[0]
    assert repeated["required"] and repeated["status"] == "deferred"
    assert records.summary()["blocking_findings"] == [initial["id"]]


@pytest.mark.parametrize("value", [-1, float("nan"), float("inf"), True])
def test_unknown_or_invalid_timing_is_not_invented(records, value):
    attempt = prepared(records)
    with pytest.raises(HarnessError, match="finite nonnegative"):
        observe(records, attempt, "prepared", started=value)
    assert records.store.get(records.run_id)["attempts"][0]["started"] is None
