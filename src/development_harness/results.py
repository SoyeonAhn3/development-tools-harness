"""Read-only, evidence-linked workflow results, including unsuccessful runs.

Reports describe recorded delivery and the files currently on disk separately.
They never accept a result, attest a manual check, or repair missing evidence.
"""

import copy
import hashlib
import json
from pathlib import Path
import sqlite3

from .files import differences, snapshot, target
from .model import HarnessError, digest
from .processes import alive
from .workflow_records import WorkflowRecords, effective_attempt


INSPECTION_ERRORS = (HarnessError, OSError, ValueError, KeyError, TypeError, sqlite3.Error)


def _location(path, *, directory=False):
    if path is None:
        return None
    path = Path(path)
    try:
        exists = path.is_dir() if directory else path.is_file()
    except OSError:
        exists = False
    return {"path": str(path), "exists": exists}


def _attempt_evidence(workflow, run, attempt):
    paths = {key: _location(attempt[key]) for key in (
        "record", "junit", "log", "stderr", "schema", "permission_report") if attempt.get(key)}
    if attempt["role"] in {"developer", "reviewer"}:
        directory = workflow.store.directory / "workflow" / run["id"] / attempt["id"]
        paths.update({name: _location(directory / filename) for name, filename in (
            ("input", "input.json"), ("attempt", "attempt.json"), ("response", "response.json"),
            ("schema", "schema.json"), ("events", "events.jsonl"), ("stderr", "stderr.log"))})
    return {"attempt_id": attempt["id"], "role": attempt["role"], "task_id": attempt["task_id"],
            "outcome": attempt.get("outcome"), "artifacts": paths}


def _patch_changes(workflow, run, patch):
    try:
        path = target(workflow.store.directory,
                      "workflow/" + run["id"] + "/patch-" + patch["attempt_id"] + "/patch.json")
        if path != Path(patch["record"]) or path.stat().st_size > 8_000_000:
            return set()
        raw = path.read_bytes()
        if hashlib.sha256(raw).hexdigest() != patch["record_hash"]:
            return set()
        record = json.loads(raw)
        return {change["path"] for change in record["proposal"]["changes"]
                if hashlib.sha256(change["content"].encode("utf-8")).hexdigest() != record["before"].get(change["path"])}
    except INSPECTION_ERRORS:
        return set()


def _delivered(workflow, run, actual):
    initial, expected = run.get("initial_expected", run["expected"]), run["expected"]
    patches = run.get("execution", {}).get("patches", [])
    changes = {patch["attempt_id"]: _patch_changes(workflow, run, patch) for patch in patches}
    result = []
    for name in differences(initial, expected):
        records = [patch for patch in patches if name in changes[patch["attempt_id"]]]
        result.append({"path": name,
            "change": "added" if name not in initial else "removed" if name not in expected else "modified",
            "before_sha256": initial.get(name), "after_sha256": expected.get(name),
            "actual_sha256": actual.get(name) if actual is not None else None,
            "current": actual is not None and actual.get(name) == expected.get(name),
            "task_ids": list(dict.fromkeys(patch["task_id"] for patch in records)),
            "patch_records": [_location(patch["record"]) for patch in records]})
    return result


def _outcome(run, recovery, attempts, inspection_error, technical_ready):
    stage = run["stage"]
    stop = run.get("execution", {}).get("stop_kind") or ""
    if stage == "cancelled":
        return "cancelled"
    if stage in {"replanning_required", "superseded"}:
        return stage
    if stage in {"technically_complete", "accepted"}:
        return "success" if technical_ready and not inspection_error else "unverified"
    if stage == "failed":
        return "failure"
    if stage == "stopped":
        return ("interrupted" if stop.endswith("interrupted") else
                "permission_failure" if stop.endswith("permission") else "failure")
    if stage == "executing" and run.get("execution", {}).get("active_step"):
        try:
            running = any(alive(attempt.get("process")) for attempt in attempts)
        except HarnessError:
            running = True  # Unknown process state cannot establish an interruption.
        if not running and (recovery.get("action") in {"retry", "reuse", "repair"} or
                            any(attempt.get("dispatch_status") == "uncertain" for attempt in attempts)):
            return "interrupted"
    return "in_progress"


def _role_metrics(attempts):
    roles = {}
    for role in ("developer", "reviewer", "validation"):
        selected = [item for item in attempts if item["role"] == role]
        durations = [item.get("duration") for item in selected]
        roles[role] = {"attempt_count": len(selected),
            "ai_dispatch_attempts": sum(item.get("actual_ai_call_attempts", 0) for item in selected),
            "confirmed_ai_calls": sum(item.get("confirmed_ai_calls") == 1 for item in selected),
            "duration": None if any(value is None for value in durations) else sum(durations),
            "observed_duration": sum(value for value in durations if value is not None)}
    return roles


def report(workflow):
    """Build a report without modifying project files, run state, or journal events."""
    run = workflow.get()
    attempts = [effective_attempt(item) for item in run["attempts"]]
    inspection_error = None
    actual = None
    try:
        actual = snapshot(workflow.project)
        workflow._check(run)
    except INSPECTION_ERRORS as exc:
        inspection_error = str(exc)
    actual_version = digest(actual) if actual is not None else None
    recovery = workflow.recovery_status()
    try:
        from .workflow_acceptance import acceptance_status
        acceptance = acceptance_status(workflow)
    except INSPECTION_ERRORS as exc:
        acceptance = {"ready": False, "accepted": False, "technical_ready": False, "blockers": [str(exc)],
                      "reuse": [], "manual": [], "completion_id": None}
    execution = run.get("execution", {})
    final_ids = set(execution.get("final_validation_ids", []))
    evidence = [_attempt_evidence(workflow, run, item) for item in attempts]
    evidence_by_id = {item["attempt_id"]: item["artifacts"] for item in evidence}
    validation = [{key: copy.deepcopy(item.get(key)) for key in (
        "id", "task_id", "check_hash", "argv", "outcome", "content_version", "tests", "exit_code",
        "reason", "failure_kind", "started", "ended", "duration", "backend")} | {
            "current": actual_version is not None and item.get("content_version") == actual_version,
            "final": item["id"] in final_ids, "evidence": evidence_by_id[item["id"]]}
        for item in attempts if item["role"] == "validation"]
    tasks = []
    for task in run["tasks"]:
        state = execution.get("task_states", {}).get(task["id"], {})
        tasks.append(copy.deepcopy(task) | {
            "completed": task["id"] in execution.get("completed_tasks", []),
            "corrections": execution.get("corrections", {}).get(task["id"], 0),
            "validation_ids": list(state.get("validation_ids", [])),
            "reviewer_attempt_id": state.get("reviewer_attempt_id"),
            "completed_content_version": state.get("completed_content_version")})
    outcome = _outcome(run, recovery, attempts, inspection_error, acceptance.get("technical_ready", False))
    reason = run.get("reason") or inspection_error
    if reason is None and outcome == "unverified" and acceptance.get("blockers"):
        reason = acceptance["blockers"][0]
    result = {
        "schema_version": 1, "kind": "workflow_result", "run_id": run["id"],
        "phase_id": run["phase_id"], "stage": run["stage"],
        "outcome": outcome, "reason": reason,
        "technical_complete": acceptance.get("technical_ready", False) and not inspection_error,
        "plan": {"planning_run_id": run["planning_run_id"], "version": run["plan_version"],
                 "hash": run["plan_hash"], "policy_hash": run["policy_hash"]},
        "content": {"initial_version": run.get("initial_content_version", run["content_version"]),
                    "recorded_version": run["content_version"], "actual_version": actual_version},
        "acceptance": copy.deepcopy(acceptance),
        "delivered_files": _delivered(workflow, run, actual),
        "unexpected_changes": differences(run["expected"], actual) if actual is not None else None,
        "partial_implementation": copy.deepcopy(execution.get("patch_pending")),
        "validation_commands": copy.deepcopy(run["policy"]["validation"]), "validation": validation,
        "reuse_evidence": copy.deepcopy(acceptance.get("reuse", [])),
        "manual_checks": copy.deepcopy(acceptance.get("manual", [])),
        "unresolved_findings": [copy.deepcopy(item) for item in run["findings"].values()
                                if item["status"] in {"open", "deferred"}],
        "feedback": copy.deepcopy(run.get("feedback", [])),
        "unresolved_feedback": [copy.deepcopy(item) for item in run.get("feedback", [])
                                if item.get("outcome") in {"correction_requested", "correction_limit",
                                                           "replanning_required", "replanning_started"}],
        "tasks": tasks,
        "metrics": WorkflowRecords(workflow.store, run["id"]).summary() | {"by_role": _role_metrics(attempts)},
        "recovery": copy.deepcopy(recovery),
        "evidence": {
            "database": _location(workflow.store.path),
            "workflow_directory": _location(workflow.store.directory / "workflow" / run["id"], directory=True),
            "planning_artifacts": [{"sha256": sha, **_location(workflow.project / name)}
                                   for name, sha in run["artifacts"].items()],
            "patch_records": [_location(patch["record"]) for patch in execution.get("patches", [])],
            "attempts": evidence,
        },
    }
    if inspection_error:
        result["inspection_error"] = inspection_error
    return result
