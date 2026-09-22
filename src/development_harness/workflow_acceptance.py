"""Version-bound final evidence, explicit human checks and result acceptance."""

import copy
import json
from pathlib import Path
import re
import sqlite3
import time

from .files import require_single_link, require_snapshot, target
from .model import HarnessError, digest, file_digest
from .processes import ensure_stopped
from .project import SECRET_PATTERN
from .workflow_records import WorkflowRecords, effective_attempt


def text(value, label):
    if not isinstance(value, str) or not value.strip() or len(value.encode("utf-8")) > 32_000:
        raise HarnessError(label + " must be nonempty bounded text.")
    if SECRET_PATTERN.search(value):
        raise HarnessError(label + " contains credential-like data.")
    return value


def validate_manual_checks(checks, plan):
    if not isinstance(checks, list) or len(checks) > 100:
        raise HarnessError("Manual checks must be a bounded array.")
    current = {r["id"] for r in plan["requirements"] if r["phase_id"] == plan["current_phase"]
               and r["disposition"] in {"implement", "reuse"}}
    seen = set()
    for item in checks:
        if not isinstance(item, dict) or set(item) != {"id", "requirement_ids", "procedure", "expected"}:
            raise HarnessError("Manual checks require id, requirement_ids, procedure and expected.")
        key = item["id"]
        if not isinstance(key, str) or not re.fullmatch(r"[A-Za-z0-9][A-Za-z0-9_-]{0,63}", key) or key in seen:
            raise HarnessError("Invalid or duplicate manual check ID.")
        seen.add(key)
        ids = item["requirement_ids"]
        if (not isinstance(ids, list) or not ids or any(not isinstance(i, str) for i in ids)
                or len(set(ids)) != len(ids) or not set(ids) <= current):
            raise HarnessError("Manual checks must reference current Phase requirements.")
        text(item["procedure"], "Manual procedure")
        text(item["expected"], "Expected result")
    return copy.deepcopy(checks)


def completion_id(run):
    return digest({"run_id": run["id"], "plan_hash": run["plan_hash"], "policy_hash": run["policy_hash"],
                   "content_version": run["content_version"],
                   "validation_ids": run.get("execution", {}).get("final_validation_ids", [])})


def binding(run):
    return {key: run[key] for key in ("plan_hash", "policy_hash", "content_version")} | {"completion_id": completion_id(run)}


def seal_validation(evidence):
    """Seal controller-produced evidence before its finished journal transition."""
    return {key: file_digest(Path(evidence[key])) for key in ("record", "junit", "log", "stderr")
            if evidence.get(key) and Path(evidence[key]).is_file()}


def _artifacts(item, required_seals):
    seals = item.get("artifact_hashes", {})
    for key in ("record", "junit"):
        if not item.get(key) or required_seals and not seals.get(key):
            raise HarnessError("Final validation lacks durable " + key + " evidence.")
    for key in set(seals) | {"record", "junit"}:
        if key not in {"record", "junit", "log", "stderr"} or not item.get(key):
            raise HarnessError("Invalid validation evidence identity.")
        path = Path(item[key])
        require_single_link(path, path.stat())
        if key in seals and file_digest(path) != seals[key]:
            raise HarnessError("Final validation evidence changed: " + key)
    path = Path(item["record"])
    if path.stat().st_size > 8_000_000:
        raise HarnessError("Validation record is too large.")
    saved = json.loads(path.read_text(encoding="utf-8"))
    for key in ("id", "content_version", "check_hash", "outcome", "tests", "exit_code", "backend", "token"):
        if saved.get(key) != item.get(key):
            raise HarnessError("Final validation artifact differs from its journal: " + key)


def final_validation(run):
    state = run.get("execution", {})
    ids = state.get("final_validation_ids", [])
    expected = {digest(check) for check in run["policy"]["validation"]}
    attempts = {a["id"]: effective_attempt(a) for a in run["attempts"]}
    if not ids or len(ids) != len(set(ids)) or len(ids) != len(expected):
        raise HarnessError("Every registered final validation check is required.")
    results = []
    last_role = max((index for index, a in enumerate(run["attempts"])
                     if a["role"] in {"developer", "reviewer"}), default=-1)
    order = {a["id"]: index for index, a in enumerate(run["attempts"])}
    latest = {a.get("check_hash"): a["id"] for a in run["attempts"]
              if a["role"] == "validation" and a["content_version"] == run["content_version"]}
    for key in ids:
        item = attempts.get(key, {})
        token = item.get("token") or {}
        if (item.get("role") != "validation" or item.get("outcome") != "passed"
                or "finished" not in item.get("journal_phases", {}) or item.get("ended") is None
                or item.get("plan_hash") != run["plan_hash"] or item.get("policy_hash") != run["policy_hash"]
                or item.get("content_version") != run["content_version"] or item.get("check_hash") not in expected
                or item.get("backend") != "appcontainer" or not isinstance(token, dict)
                or token.get("appcontainer") is not True or token.get("elevated") is not False
                or type(token.get("capability_count")) is not int or token["capability_count"] != 0
                or type(item.get("tests")) is not int or item["tests"] < 1 or item.get("exit_code") != 0
                or order.get(key, -1) <= last_role or latest.get(item.get("check_hash")) != key):
            raise HarnessError("Final validation is missing, incomplete, failing or stale: " + key)
        _artifacts(item, True)
        results.append(item)
    if {a["check_hash"] for a in results} != expected:
        raise HarnessError("Final validation omits a registered check.")
    return results


def _technical(workflow, run):
    workflow._check(run)
    if run["policy"].get("result_version") != 1:
        raise HarnessError("Legacy results lack approved acceptance policy and sealed evidence; prepare a new approved workflow.")
    if run["stage"] not in {"technically_complete", "accepted"} or not run.get("approval"):
        raise HarnessError("Technical completion with execution approval is required before result acceptance.")
    ensure_stopped([effective_attempt(a) for a in run["attempts"]])
    state = run.get("execution", {})
    if (state.get("in_flight") or state.get("active_step") or state.get("patch_pending") or workflow._pending(run)
            or state.get("completed_tasks") != [t["id"] for t in run["tasks"]]
            or state.get("stage") != "complete" or state.get("final_content_version") != run["content_version"]):
        raise HarnessError("Incomplete execution records prevent result acceptance.")
    if WorkflowRecords(workflow.store, run["id"]).summary()["blocking_findings"]:
        raise HarnessError("Mandatory review findings remain unresolved.")
    attempts = {a["id"]: effective_attempt(a) for a in run["attempts"]}
    for task in run["tasks"]:
        task_state = state["task_states"].get(task["id"], {})
        review = attempts.get(task_state.get("reviewer_attempt_id"), {})
        if (review.get("role") != "reviewer" or review.get("task_id") != task["id"]
                or review.get("outcome") != "validated" or review.get("review_verdict") != "pass"
                or not review.get("findings_ingested") or "finished" not in review.get("journal_phases", {})
                or review.get("content_version") != task_state.get("completed_content_version")):
            raise HarnessError("A completed Task lacks its independent passing review: " + task["id"])
        path = target(workflow.store.directory, "workflow/" + run["id"] + "/" + review["id"] + "/response.json")
        require_single_link(path, path.stat())
        if path.stat().st_size > 5_000_000:
            raise HarnessError("Reviewer response exceeds its evidence limit.")
        response = json.loads(path.read_text(encoding="utf-8"))
        if (digest(response) != review.get("response_hash") or response.get("task_id") != task["id"]
                or response.get("verdict") != "pass"):
            raise HarnessError("Independent review evidence changed: " + task["id"])
    completions = [event for event in workflow.store.events(run["id"]) if event["kind"] == "workflow_technically_complete"]
    if not completions or completions[-1]["data"] != {
            "content_version": run["content_version"], "validation_ids": state["final_validation_ids"]}:
        raise HarnessError("Final evidence does not match the durable technical-completion event.")
    if any(f.get("outcome") in {"correction_requested", "correction_limit", "replanning_required", "replanning_started"}
           for f in run.get("feedback", [])):
        raise HarnessError("Unresolved user feedback prevents result acceptance.")
    checks = final_validation(run)
    require_snapshot(workflow.project, run["expected"])
    return checks


def _current(record, run):
    return all(record.get(k) == v for k, v in binding(run).items())


def acceptance_status(workflow):
    run = workflow.get()
    result = {"ready": False, "accepted": False, "technical_ready": False, "blockers": [], "reuse": [], "manual": [],
              "completion_id": completion_id(run)}
    try:
        checks = _technical(workflow, run)
        result["technical_ready"] = True
    except (HarnessError, OSError, ValueError, KeyError, TypeError, sqlite3.Error) as exc:
        result["blockers"].append(str(exc))
        checks = []
    final_ids = {a["id"] for a in checks}
    for req in run["plan"]["requirements"]:
        if req["phase_id"] != run["phase_id"] or req["disposition"] != "reuse":
            continue
        records = [r for r in run.get("reuse_evidence", []) if r["requirement_id"] == req["id"]]
        last = records[-1] if records else None
        status = "missing" if last is None else "stale" if not _current(last, run) else last["outcome"]
        if status == "passed" and (not last.get("validation_ids") or not set(last["validation_ids"]) <= final_ids):
            status = "unverified"
        result["reuse"].append({"requirement_id": req["id"], "text": req["text"], "verification": req["verification"],
                               "status": status, "evidence": copy.deepcopy(last)})
        if status != "passed":
            result["blockers"].append("Reuse requirement " + req["id"] + " is " + status + ".")
    for definition in run["policy"].get("manual_checks", []):
        records = [r for r in run.get("manual_checks", []) if r["check_id"] == definition["id"]]
        last = records[-1] if records else None
        status = "missing" if last is None else "stale" if not _current(last, run) else last["outcome"]
        result["manual"].append(copy.deepcopy(definition) | {"status": status, "evidence": copy.deepcopy(last)})
        if status != "passed":
            result["blockers"].append("Manual check " + definition["id"] + " is " + status + ".")
    result["ready"] = not result["blockers"]
    accepted = run.get("acceptance")
    if run["stage"] == "accepted":
        if not accepted or accepted.get("scope") != "result_acceptance" or not _current(accepted, run):
            result["blockers"].append("Result acceptance does not match the current evidence.")
            result["ready"] = False
        result["accepted"] = result["ready"]
    return result


def _record(workflow, collection, subject, value, outcome, evidence, *, validation_ids=None, record_id=None):
    run = workflow.get()
    checks = _technical(workflow, run)
    if run["stage"] != "technically_complete":
        raise HarnessError("Accepted results cannot receive replacement confirmation evidence.")
    if outcome not in {"passed", "failed"}:
        raise HarnessError("Confirmation outcome must be passed or failed.")
    text(evidence, "Confirmation evidence")
    detail = {subject: value, "outcome": outcome, "evidence": evidence, **binding(run), "source": "user"}
    if collection == "reuse_evidence":
        ids = [r["id"] for r in run["plan"]["requirements"] if r["phase_id"] == run["phase_id"] and r["disposition"] == "reuse"]
        if value not in ids:
            raise HarnessError("Reuse evidence must name a current reused requirement.")
        if (not isinstance(validation_ids, list) or not validation_ids or any(not isinstance(i, str) for i in validation_ids)
                or len(set(validation_ids)) != len(validation_ids)
                or not set(validation_ids) <= {a["id"] for a in checks}):
            raise HarnessError("Reuse evidence requires actual passing final validation IDs.")
        detail["validation_ids"] = validation_ids
        detail["check_hashes"] = [next(a["check_hash"] for a in checks if a["id"] == i) for i in validation_ids]
    elif value not in {c["id"] for c in run["policy"].get("manual_checks", [])}:
        raise HarnessError("Manual evidence must name a check pinned before execution approval.")
    key = record_id or digest(detail)
    if not isinstance(key, str) or not re.fullmatch(r"[A-Za-z0-9][A-Za-z0-9_-]{0,127}", key):
        raise HarnessError("Invalid confirmation record ID.")
    def save(current):
        current.setdefault(collection, []).append({"id": key, **detail, "at": time.time()})
    return workflow.store.transition(run["id"], run["id"] + ":" + collection + ":" + key,
                                     "workflow_" + collection, detail, save)


def record_reuse(workflow, requirement_id, validation_ids, evidence, *, outcome="passed", record_id=None):
    return _record(workflow, "reuse_evidence", "requirement_id", requirement_id, outcome, evidence,
                   validation_ids=validation_ids, record_id=record_id)


def record_manual(workflow, check_id, outcome, evidence, *, record_id=None):
    return _record(workflow, "manual_checks", "check_id", check_id, outcome, evidence, record_id=record_id)


def accept(workflow):
    run = workflow.get()
    gate = acceptance_status(workflow)
    if not gate["ready"]:
        raise HarnessError("Result acceptance blocked: " + "; ".join(gate["blockers"]))
    if run["stage"] == "accepted":
        return run
    detail = {"scope": "result_acceptance", **binding(run),
              "validation_ids": run["execution"]["final_validation_ids"],
              "reuse_evidence_ids": [r["evidence"]["id"] for r in gate["reuse"]],
              "manual_check_ids": [r["evidence"]["id"] for r in gate["manual"]]}
    def accepted(current):
        now = time.time()
        current.update(stage="accepted", reason=None, acceptance=detail | {"at": now})
        for wait in current["waits"]:
            if wait["reason"] == "result_acceptance" and wait["ended"] is None:
                wait.update(ended=now, duration=now - wait["started"] if now >= wait["started"] else None)
    return workflow.store.transition(run["id"], run["id"] + ":accepted:" + completion_id(run),
                                     "workflow_result_accepted", detail, accepted)
