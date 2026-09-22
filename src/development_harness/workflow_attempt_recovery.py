"""Reconcile controller-owned attempt artifacts without making external calls.

The caller holds the project lock, verifies authorization and content, and proves
that no recorded process survives. This module never applies files or findings.
"""

import copy
import hashlib
import json
from pathlib import Path

from .codex_adapter import DISABLED_CODE_MODE_NOTICE, parse_events
from .files import require_single_link, target
from .isolated_validation import review_evidence
from .model import HarnessError, digest
from .project import MAX_CONTEXT_BYTES, SECRET_PATTERN, decode_json
from .worker_contract import (DEVELOPER_SCHEMA, REVIEWER_SCHEMA, REVIEWER_FOLLOWUP_SCHEMA,
                              validate_proposal, validate_review)
from .workflow_records import WorkflowRecords, effective_attempt, validate_recovery_observations


def _read(directory, name, *, optional=False, limit=5_000_000):
    path = target(directory, name)
    if not path.exists() and optional:
        return None, None
    try:
        metadata = path.stat()
        require_single_link(path, metadata)
        if metadata.st_size > limit:
            raise HarnessError("Recovery artifact exceeds its bounded size: " + name)
        raw = path.read_bytes()
        after = path.stat()
        if (metadata.st_size, metadata.st_mtime_ns) != (after.st_size, after.st_mtime_ns):
            raise HarnessError("Recovery artifact changed while reading: " + name)
        return raw.decode("utf-8"), hashlib.sha256(raw).hexdigest()
    except (OSError, UnicodeError) as exc:
        raise HarnessError("Missing or unreadable recovery artifact: " + name) from exc


def _json(directory, name, *, optional=False):
    raw, sha = _read(directory, name, optional=optional)
    return (None if raw is None else decode_json(raw)), sha


def _identity(attempt, saved):
    if not isinstance(saved, dict):
        raise HarnessError("Saved attempt is not a controller record.")
    for key in ("id", "role", "task_id", "content_version", "plan_hash", "policy_hash", "input_hash"):
        if saved.get(key) != attempt.get(key):
            raise HarnessError("Saved attempt identity differs from the journal: " + key)
    for key in ("process", "containment", "started", "ended", "duration", "session_id", "response_hash", "usage", "cost",
                "review_prior_findings", "review_prior_findings_hash", "review_assessments_hash",
                "prepared_at", "process_registered_at", "dispatch_intent_at", "responded_at", "finished_at"):
        if attempt.get(key) is not None and saved.get(key) != attempt[key]:
            raise HarnessError("Saved artifact contradicts a journal observation: " + key)


def _packet(run, attempt, packet, scope):
    if not isinstance(packet, dict) or digest(packet) != attempt.get("input_hash"):
        raise HarnessError("Saved worker input does not match its journal hash.")
    expected = scope.packet()
    for key, value in expected.items():
        if packet.get(key) != value:
            raise HarnessError("Saved worker input differs from the original Task scope: " + key)
    if attempt["content_version"] != digest(scope.baseline):
        raise HarnessError("Saved response belongs to a different content version.")
    for item in packet["files"]:
        name, text, sha = item["path"], item["text"], item["sha256"]
        if (sha != scope.baseline.get(name, "absent") or
                (sha == "absent" and text != "") or
                (sha != "absent" and hashlib.sha256(text.encode("utf-8")).hexdigest() != sha)):
            raise HarnessError("Saved input files do not match the original content identity.")
    raw = json.dumps(packet, ensure_ascii=False)
    if len(raw.encode("utf-8")) > MAX_CONTEXT_BYTES * 2 or SECRET_PATTERN.search(raw):
        raise HarnessError("Saved input exceeds the worker budget or contains credential-like data.")
    allowed = set(expected) | ({"feedback"} if attempt["role"] == "developer" else
                               {"before", "validation", "prior_findings"})
    if set(packet) - allowed:
        raise HarnessError("Saved worker input contains unsupported fields.")
    if attempt["role"] == "developer":
        feedback = run.get("execution", {}).get("task_states", {}).get(attempt["task_id"], {}).get("feedback")
        if packet.get("feedback") != feedback:
            raise HarnessError("Saved Developer feedback differs from the controller state.")
        return []
    state = run.get("execution", {}).get("task_states", {}).get(attempt["task_id"], {})
    if packet.get("before") != state.get("before", scope.packet()["files"]):
        raise HarnessError("Saved Reviewer before-files differ from the controller baseline.")
    order = {item["id"]: index for index, item in enumerate(run["attempts"])}
    candidates = [effective_attempt(item) for item in run["attempts"]
                  if item["role"] == "validation" and item["task_id"] == attempt["task_id"] and
                  item["content_version"] == attempt["content_version"] and order[item["id"]] < order[attempt["id"]]]
    by_check = {item["check_hash"]: item for item in candidates if item.get("check_hash")}
    checks = run["policy"]["validation"]
    if (set(by_check) != {digest(check) for check in checks} or
            any(item.get("outcome") != "passed" or "finished" not in item.get("journal_phases", {})
                for item in by_check.values())):
        raise HarnessError("Saved Reviewer lacks the latest passing registered validation.")
    validation = [review_evidence(by_check[digest(check)]) for check in checks]
    if (packet.get("validation") != validation or
            (state.get("validation_ids") is not None and
             {item["id"] for item in validation} != set(state["validation_ids"]))):
        raise HarnessError("Saved Reviewer validation differs from the controller batch.")
    fields = ("id", "task_id", "requirement_id", "path", "required", "status", "evidence", "recommendation", "severity")
    prior = ([{key: item[key] for key in fields} for _, item in sorted(run["findings"].items())
              if item["task_id"] == attempt["task_id"] and item["status"] in {"open", "deferred"}]
             if not attempt.get("findings_ingested") else attempt.get("review_prior_findings", []))
    if packet.get("prior_findings", []) != prior:
        raise HarnessError("Saved Reviewer prior findings differ from the controller record.")
    return prior


def _decision(workflow, attempt, disposition, evidence, observations, response, commit):
    validate_recovery_observations(attempt, observations)
    records = WorkflowRecords(workflow.store, workflow.get()["id"])
    existing = attempt.get("recovery")
    decision = {"attempt_id": attempt["id"], "disposition": disposition,
                "evidence": evidence, "observations": observations}
    if existing and any(existing.get(key) != value for key, value in decision.items()):
        raise HarnessError("Recovery artifacts differ from the recorded reconciliation.")
    if commit:
        reconciled = records.recover_attempt(attempt["id"], disposition=disposition,
                                             evidence=evidence, observations=observations)
    else:
        reconciled = effective_attempt({**attempt, "recovery": existing or decision})
    return {"action": "reuse" if disposition == "validated" else "retry",
            "response": response, "attempt": reconciled}


def reconcile_attempt(workflow, attempt_id, *, scope=None, commit=True):
    """Inspect/reconcile one attempt; ``commit=False`` makes no journal mutation."""
    run = workflow.get()
    attempt = next((item for item in run["attempts"] if item["id"] == attempt_id), None)
    if attempt is None:
        raise HarnessError("Unknown attempt for recovery.")
    if (attempt.get("plan_hash") != run["plan_hash"] or attempt.get("policy_hash") != run["policy_hash"]):
        raise HarnessError("Attempt does not match the approved plan and policy.")
    if attempt["role"] == "validation":
        if attempt.get("outcome") in {"passed", "failed"} and "finished" in attempt.get("journal_phases", {}):
            raise HarnessError("Completed validation must not be reclassified as interrupted.")
        evidence = {"reason": "Interrupted or unverified validation must run again after process reconciliation.",
                    "original_outcome": attempt.get("outcome")}
        return _decision(workflow, attempt, "validation_interrupted", evidence, {}, None, commit)
    if attempt["role"] not in {"developer", "reviewer"}:
        raise HarnessError("Unknown workflow role in recovery.")
    directory = target(workflow.store.directory, "workflow/" + run["id"] + "/" + attempt_id)
    # The transport cannot transmit stdin until the durable intent callback
    # returns. A local intent artifact can precede a failed journal callback.
    unsent = ("dispatch_intent" not in attempt.get("journal_phases", {}) and
              attempt.get("responded_at") is None and attempt.get("confirmed_ai_calls") != 1)
    if unsent:
        events, _ = _read(directory, "events.jsonl", optional=True)
        if target(directory, "response.json").exists():
            raise HarnessError("An unsent journal contradicts a saved AI response; inspection is required.")
        for line in (events or "").splitlines():
            event = decode_json(line)
            if (not isinstance(event, dict) or event.get("type") in {"turn.started", "turn.completed"} or
                    isinstance(event.get("item"), dict) and event["item"].get("type") == "agent_message"):
                raise HarnessError("Unsent journal contradicts transport output; automatic redispatch is blocked.")
        return _decision(workflow, attempt, "not_sent", {"reason": "No durable dispatch intent or response observation."},
                         {}, None, commit)
    saved, saved_hash = _json(directory, "attempt.json")
    _identity(attempt, saved)
    packet, packet_hash = _json(directory, "input.json")
    response, response_hash = _json(directory, "response.json")
    schema, schema_hash = _json(directory, "schema.json")
    raw_events, events_hash = _read(directory, "events.jsonl")
    scope = scope or workflow._scope(run, attempt["task_id"])
    prior = _packet(run, attempt, packet, scope)
    expected_schema = DEVELOPER_SCHEMA if attempt["role"] == "developer" else (
        REVIEWER_FOLLOWUP_SCHEMA if prior else REVIEWER_SCHEMA)
    if schema != expected_schema or saved.get("exit_code") != 0:
        raise HarnessError("Saved response lacks the registered schema or successful transport completion.")
    for key, name in (("log", "events.jsonl"), ("schema", "schema.json"), ("stderr", "stderr.log")):
        if saved.get(key) is not None and Path(saved[key]) != directory / name:
            raise HarnessError("Saved artifact path leaves its controller attempt directory.")
    if saved.get("policy", {}).get("profile") != run["policy"].get("worker_boundary", "text-only-v1"):
        raise HarnessError("Saved response lacks the approved worker capability boundary.")
    parsed, usage = parse_events(raw_events, allowed_notices=(DISABLED_CODE_MODE_NOTICE,))
    sessions = [decode_json(line).get("thread_id") for line in raw_events.splitlines()
                if decode_json(line).get("type") == "thread.started"]
    if (len(sessions) != 1 or not isinstance(sessions[0], str) or not sessions[0] or parsed != response or
            saved.get("response_hash") != digest(response) or saved.get("session_id") != sessions[0]):
        raise HarnessError("Saved response and confirmed transport session do not agree.")
    if any(effective_attempt(item).get("session_id") == sessions[0] for item in run["attempts"] if item["id"] != attempt_id):
        raise HarnessError("Recovered worker session repeats a previous role session.")
    if saved.get("usage") != usage:
        raise HarnessError("Saved usage differs from the confirmed event stream.")
    if attempt["role"] == "developer":
        validate_proposal(response, scope)
    else:
        validate_review(response, scope, prior_findings=prior)
    observations = {key: copy.deepcopy(saved[key]) for key in (
        "input_hash", "process", "containment", "started", "ended", "duration", "session_id", "response_hash", "usage", "cost",
        "prepared_at", "process_registered_at", "dispatch_intent_at", "responded_at", "finished_at")
        if saved.get(key) is not None}
    if attempt["role"] == "reviewer":
        observations.update(review_verdict=response["verdict"], review_findings_hash=digest(response["findings"]),
                            review_validation_ids=[item["id"] for item in packet["validation"]],
                            review_validation_hashes=[digest(item) for item in packet["validation"]])
        if prior:
            observations.update(review_prior_findings=copy.deepcopy(prior), review_prior_findings_hash=digest(prior),
                                review_assessments_hash=digest(response["assessments"]))
        for key, value in observations.items():
            if saved.get(key) is not None and saved[key] != value:
                raise HarnessError("Saved review metadata contradicts the validated response: " + key)
    evidence = {"artifacts": {"attempt.json": saved_hash, "input.json": packet_hash, "response.json": response_hash,
                              "schema.json": schema_hash, "events.jsonl": events_hash}}
    return _decision(workflow, attempt, "validated", evidence, observations, response, commit)
