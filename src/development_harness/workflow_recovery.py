"""Explicit recovery of a proven interrupted boundary, never blind redispatch."""

import copy
import hashlib
import json
from pathlib import Path
import sqlite3
import time

from .files import apply_write, require_single_link, require_snapshot, snapshot, target
from .model import HarnessError, digest
from .processes import ProjectLock, ensure_stopped
from .workflow_attempt_recovery import reconcile_attempt
from .workflow_records import WorkflowRecords, effective_attempt
from .worker_contract import save_record, validate_proposal


TERMINAL = {"cancelled", "failed", "technically_complete", "accepted", "superseded", "replanning_required"}


def _completed_check(record):
    item = effective_attempt(record)
    return ("finished" in item.get("journal_phases", {}) and
            (item.get("outcome") in {"passed", "failed"} or
             item.get("ended") is not None and item.get("outcome") != "interrupted"))


def _read(path):
    require_single_link(path, path.stat())
    if path.stat().st_size > 8_000_000:
        raise HarnessError("Recovery artifact exceeds its size limit.")
    try:
        return json.loads(path.read_text(encoding="utf-8"))
    except (ValueError, UnicodeError) as exc:
        raise HarnessError("Recovery artifact is incomplete or invalid: " + str(path)) from exc


def _scope(workflow, run, attempt):
    scope = workflow._scope(run, attempt["task_id"])
    if attempt["content_version"] != run["content_version"]:
        raise HarnessError("Interrupted attempt belongs to different content.")
    path = target(workflow.store.directory, "workflow/" + run["id"] + "/" + attempt["id"] + "/input.json")
    if path.exists():
        packet = _read(path)
        scope.files = copy.deepcopy(packet["files"])
    scope.baseline = copy.deepcopy(run["expected"])
    return scope


def _patch(workflow, run, attempt, response):
    pending = run["execution"]["patch_pending"]
    directory = target(workflow.store.directory, "workflow/" + run["id"] + "/patch-" + attempt["id"])
    if (pending.get("attempt_id") != attempt["id"] or pending.get("task_id") != attempt["task_id"] or
            pending.get("before") != run["content_version"] or Path(pending.get("directory", "")) != directory):
        raise HarnessError("Pending patch identity does not match the interrupted Developer.")
    before = run["expected"]
    after = dict(before)
    applied = []
    for change in response["changes"]:
        after[change["path"]] = hashlib.sha256(change["content"].encode("utf-8")).hexdigest()
        applied.append({"path": change["path"], "sha256": after[change["path"]]})
    path = target(workflow.store.directory, directory.relative_to(workflow.store.directory).as_posix() + "/patch.json")
    if path.exists():
        record = _read(path)
        if (record.get("task_id") != attempt["task_id"] or record.get("before") != before or
                record.get("proposal") != response or record.get("outcome") not in {"prepared", "partial", "applied"} or
                not isinstance(record.get("applied"), list) or
                record["applied"] != applied[:len(record["applied"]) ]):
            raise HarnessError("Pending patch evidence does not match the saved response.")
        if record["outcome"] == "applied" and (record.get("after") != after or record.get("content_version") != digest(after)):
            raise HarnessError("Completed patch evidence has a different content identity.")
    else:
        # The intent is durable before the patch directory/record is created;
        # no file may have changed before the initial patch record is saved.
        require_snapshot(workflow.project, before)
        record = {"task_id": attempt["task_id"], "before": before, "proposal": response,
                  "applied": [], "outcome": "prepared"}
    _partial_files(workflow.project, before, after)
    return {"directory": directory, "record": record, "before": before, "after": after, "applied": applied}


def _partial_files(project, before, after):
    actual = snapshot(project)
    changed = [name for name in set(actual) | set(before) | set(after)
               if actual.get(name) not in {before.get(name), after.get(name)}]
    if changed:
        raise HarnessError("Unexpected partial or user-edited files; preserved: " + ", ".join(sorted(changed)))
    return actual


def _assess(workflow):
    run = workflow.get()
    state = run.get("execution", {})
    result = {"available": False, "action": "blocked", "stage": state.get("stage"),
              "task_id": None, "reason": "", "advisory": True}
    if run["stage"] in TERMINAL:
        return result | {"action": "terminal", "reason": "This terminal workflow cannot be restarted."}, {}
    workflow._check(run, check_files=False)
    if not run.get("approval"):
        raise HarnessError("Execution approval is required before recovery.")
    if run["stage"] == "stopped" and state.get("stop_kind") not in {
            "interrupted", "final_interrupted", "execution_error", "permission"}:
        raise HarnessError("This stop requires its reported issue to be resolved; it is not interrupted recovery.")
    ensure_stopped([effective_attempt(item) for item in run["attempts"]])
    active = state.get("active_step")
    if not active:
        workflow._check(run)
        if state.get("in_flight") or state.get("patch_pending") or workflow._pending(run):
            raise HarnessError("Incomplete legacy boundary lacks the recorded recovery cursor; inspection required.")
        return result | {"available": True, "action": "continue", "reason": "Continue from the completed boundary."}, {}
    task = run["tasks"][min(state["task_index"], len(run["tasks"]) - 1)]
    stage, task_id = active["stage"], active["task_id"]
    if (stage != state["stage"] or task_id != task["id"] or
            not set(task["depends_on"]) <= set(state["completed_tasks"])):
        raise HarnessError("Interrupted boundary no longer matches the approved Task order.")
    events = workflow.store.events(run["id"])
    marker = next((event for event in events if event["id"] == run["id"] + ":execution:" + active["id"]), None)
    if not marker or marker["kind"] != "execution_step_started" or marker["data"] != {"stage": stage, "task_id": task_id}:
        raise HarnessError("Interrupted boundary has no matching durable start event.")
    before_ids = active["before_attempt_ids"]
    if [item["id"] for item in run["attempts"][:len(before_ids)]] != before_ids:
        raise HarnessError("Interrupted boundary attempt history changed.")
    attempts = run["attempts"][len(before_ids):]
    prior = dict(run, attempts=run["attempts"][:len(before_ids)])
    if workflow._pending(prior):
        raise HarnessError("An earlier unresolved attempt prevents recovery.")
    role = {"developer": "developer", "review": "reviewer", "validation": "validation", "final_validation": "validation"}.get(stage)
    if not role or any(item["role"] != role or item["task_id"] != task_id or
                       item["content_version"] != run["content_version"] for item in attempts):
        raise HarnessError("Interrupted attempts do not belong to the current boundary.")
    result.update(stage=stage, task_id=task_id)
    context = {"run": run, "active": active, "attempts": attempts}
    if role == "validation":
        workflow._check(run)
        # A code failure must still consume its normal correction decision.
        # Other finished failures never become successful through recovery.
        completed_failure = next((effective_attempt(item) for item in attempts if _completed_check(item) and
                                  effective_attempt(item).get("outcome") != "passed"), None)
        context["failure"] = completed_failure
        for item in attempts:
            if not _completed_check(item):
                reconcile_attempt(workflow, item["id"], commit=False)
        return result | {"available": True, "action": "retry", "reason": "Reconcile the interrupted check and rerun required validation."}, context
    if len(attempts) > 1:
        raise HarnessError("More than one role attempt belongs to an interrupted boundary.")
    if not attempts:
        if state.get("patch_pending"):
            raise HarnessError("A pending patch has no recorded Developer attempt.")
        workflow._check(run)
        return result | {"available": True, "action": "retry", "reason": "No role attempt was dispatched at this boundary."}, context
    attempt = attempts[0]
    scope = _scope(workflow, run, attempt)
    recovered = reconcile_attempt(workflow, attempt["id"], scope=scope, commit=False)
    context.update(scope=scope, recovered=recovered)
    action = recovered["action"]
    if state.get("patch_pending"):
        if role != "developer" or action != "reuse":
            raise HarnessError("A pending patch requires a verified Developer response.")
        validate_proposal(recovered["response"], scope)
        context["patch"] = _patch(workflow, run, recovered["attempt"], recovered["response"])
        action = "repair"
    else:
        workflow._check(run)
    return result | {"available": True, "action": action, "reason":
        "Reuse the verified saved response." if action == "reuse" else
        "Finish only the proven unapplied file changes." if action == "repair" else
        "The recorded request was not sent; retry is permitted."}, context


def recovery_status(workflow):
    try:
        return _assess(workflow)[0]
    except (HarnessError, OSError, ValueError, KeyError, TypeError, sqlite3.Error) as exc:
        return {"available": False, "action": "blocked", "reason": str(exc), "advisory": True}


def _finish(workflow):
    run = workflow.get()
    for item in run.get("recoveries", []):
        if item["status"] != "started":
            continue
        def done(current):
            record = next(value for value in current["recoveries"] if value["id"] == item["id"])
            record.update(status="completed", ended=time.time(), next_stage=current["execution"]["stage"])
        workflow.store.transition(run["id"], run["id"] + ":recovery:" + item["id"] + ":finished",
                                  "workflow_recovery_finished", {}, done)


def _repair(workflow, engine, context, recovered):
    patch = context["patch"]
    directory, before, after = patch["directory"], patch["before"], patch["after"]
    directory.mkdir(parents=True, exist_ok=True)
    record = patch["record"]
    # Preserve an existing patch record until each checked write is durable.
    if not (directory / "patch.json").exists():
        save_record(directory / "patch.json", record)
    applied = []
    for change in recovered["response"]["changes"]:
        actual = _partial_files(workflow.project, before, after)
        name = change["path"]
        if actual.get(name) != after[name]:
            require_snapshot(workflow.project, actual)
            apply_write(workflow.project, name, change["content"], before.get(name))
            actual[name] = after[name]
            require_snapshot(workflow.project, actual)
        applied.append({"path": name, "sha256": after[name]})
        record.update(applied=list(applied), outcome="partial")
        save_record(directory / "patch.json", record)
    require_snapshot(workflow.project, after)
    record.update(outcome="applied", applied=patch["applied"], after=after, content_version=digest(after))
    save_record(directory / "patch.json", record)
    engine.commit_patch(context["active"]["task_id"], recovered["attempt"]["id"], directory, record)


def resume(workflow, *, worker_factory, validator_factory, codex_path=None, steps=None):
    from .workflow_execution import Execution, execute
    if steps is not None and (type(steps) is not int or steps < 1):
        raise HarnessError("steps must be a positive integer.")
    with ProjectLock(workflow.store):
        assessment, context = _assess(workflow)
        if assessment["action"] == "terminal":
            return workflow.get()
        if not assessment["available"]:
            raise HarnessError(assessment["reason"])
        if not context:
            _finish(workflow)
            return execute(workflow, worker_factory=worker_factory, validator_factory=validator_factory,
                           codex_path=codex_path, steps=steps, _locked=True)
        run, active = context["run"], context["active"]
        # A recovery may itself stop after it creates patch intent: its next
        # action changes from reuse to repair, but it remains the same boundary.
        detail = {key: assessment[key] for key in ("stage", "task_id")}
        def starting(current):
            current.setdefault("recoveries", []).append({"id": active["id"], **detail, "action": assessment["action"],
                "status": "started", "started": time.time(), "ended": None})
            current.update(stage="executing", reason=None)
            current["execution"].update(stop_kind=None, ended=None)
        workflow.store.transition(run["id"], run["id"] + ":recovery:" + active["id"] + ":started",
                                  "workflow_recovery_started", detail, starting)
        engine = Execution(workflow, worker_factory, validator_factory, codex_path)
        stage, task_id = active["stage"], active["task_id"]
        if stage in {"validation", "final_validation"}:
            for attempt in context["attempts"]:
                if not _completed_check(attempt):
                    reconcile_attempt(workflow, attempt["id"])
            failure = context.get("failure")
            if failure:
                kind = failure.get("failure_kind") or ("code" if failure["outcome"] == "failed" else "validation_incomplete")
                reason = failure.get("reason") or "Required validation failed."
                if stage == "validation" and kind == "code":
                    from .isolated_validation import review_evidence
                    engine.correction(task_id, reason, [review_evidence(failure)])
                else:
                    engine.stop("final_" + kind if stage == "final_validation" else kind, reason, failed=kind == "code")
            else:
                def reset(current):
                    if stage == "final_validation":
                        current["execution"]["final_validation_ids"] = []
                    else:
                        current["execution"]["task_states"][task_id]["validation_ids"] = []
                engine.boundary(stage, reset)
        elif context["attempts"]:
            recovered = reconcile_attempt(workflow, context["attempts"][0]["id"], scope=context["scope"])
            if recovered["action"] == "retry":
                engine.boundary(stage)
            elif stage == "developer":
                if "patch" in context:
                    _repair(workflow, engine, context, recovered)
                else:
                    engine.apply_developer(task_id, recovered)
            else:
                records = WorkflowRecords(workflow.store, run["id"])
                attempt = recovered["attempt"]
                if attempt.get("review_prior_findings"):
                    records.apply_review_assessments(attempt["id"], recovered["response"])
                else:
                    records.ingest_findings(attempt["id"], recovered["response"]["findings"])
                engine.review_result(task_id, recovered)
        else:
            engine.boundary(stage)
        _finish(workflow)
        if steps == 1 or workflow.get()["stage"] != "executing":
            return workflow.get()
        return execute(workflow, worker_factory=worker_factory, validator_factory=validator_factory,
                       codex_path=codex_path, steps=None if steps is None else steps - 1, _locked=True)
