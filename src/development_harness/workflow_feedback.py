"""Durable user feedback routing within a version-bound approved Phase.

The caller holds ProjectLock. Submission records a decision but never dispatches
workers, applies files, or silently approves a replacement plan.
"""

import copy
import re
import time

from .model import HarnessError, digest
from .processes import ensure_stopped
from .project import SECRET_PATTERN
from .workflow_records import effective_attempt


MAX_FEEDBACK_BYTES = 32_000
FEEDBACK_KINDS = {"defect", "requirements"}
TERMINAL = {"accepted", "cancelled", "superseded"}


def _payload(text, kind, task_id):
    if (not isinstance(text, str) or not text.strip() or "\0" in text or
            len(text.encode("utf-8")) > MAX_FEEDBACK_BYTES or SECRET_PATTERN.search(text)):
        raise HarnessError("Feedback must be nonempty bounded text without credential-like data.")
    if not isinstance(kind, str) or kind not in FEEDBACK_KINDS:
        raise HarnessError("Feedback kind must be defect or requirements.")
    if task_id is not None and (not isinstance(task_id, str) or not task_id.strip()):
        raise HarnessError("Feedback task identity must be nonempty text.")
    if kind == "defect" and task_id is None:
        raise HarnessError("Same-scope defect feedback must identify an approved Task.")
    return {"kind": kind, "text": text, "task_id": task_id}


def _previous_completion(run):
    execution = run.get("execution", {})
    fields = ("before_content_version", "validation_ids", "developer_attempt_id", "reviewer_attempt_id",
              "completed_content_version")
    return {"stage": run["stage"], "content_version": run["content_version"],
            "attempt_ids": [item["id"] for item in run["attempts"]],
            "execution_stage": execution.get("stage"), "task_index": execution.get("task_index"),
            "completed_tasks": copy.deepcopy(execution.get("completed_tasks", [])),
            "final_validation_ids": copy.deepcopy(execution.get("final_validation_ids", [])),
            "final_content_version": execution.get("final_content_version"), "ended": execution.get("ended"),
            "task_states": {identity: {key: copy.deepcopy(state[key]) for key in fields if key in state}
                            for identity, state in execution.get("task_states", {}).items()}}


def _existing(run, payload, feedback_id):
    history = run.get("feedback", [])
    if feedback_id is not None:
        item = next((item for item in history if item["id"] == feedback_id), None)
        if item is not None and any(item.get(key) != value for key, value in payload.items()):
            raise HarnessError("Feedback identity was reused with different original text or routing.")
        return item
    # A retry immediately after the routing transaction must not consume the
    # allowance again just because that transaction advanced the sequence.
    if history:
        item = history[-1]
        if (all(item.get(key) == value for key, value in payload.items()) and
                item.get("plan_hash") == run["plan_hash"] and
                item.get("outcome") in {"correction_requested", "correction_limit", "replanning_required"}):
            return item
    return None


def submit_feedback(workflow, text, *, kind, task_id=None, feedback_id=None):
    """Persist the exact feedback and its route; the caller already holds the lock."""
    payload = _payload(text, kind, task_id)
    if feedback_id is not None and (not isinstance(feedback_id, str) or
            not re.fullmatch(r"[A-Za-z0-9][A-Za-z0-9_-]{0,127}", feedback_id)):
        raise HarnessError("Feedback identity must be a bounded identifier.")
    run = workflow.get()
    if _existing(run, payload, feedback_id) is not None:
        return run
    if run["stage"] in TERMINAL:
        raise HarnessError("Accepted, cancelled or superseded workflows cannot be reopened by feedback.")
    workflow._check(run, check_files=kind == "defect")
    if not run.get("approval"):
        raise HarnessError("Execution authorization is required before result feedback.")
    execution = run.get("execution")
    if not isinstance(execution, dict):
        raise HarnessError("Execute the approved Phase before submitting result feedback.")
    if execution.get("in_flight") or execution.get("patch_pending") or workflow._pending(run):
        raise HarnessError("Recover incomplete attempts or partial files before routing feedback.")
    ensure_stopped([effective_attempt(item) for item in run["attempts"]])
    task_ids = [task["id"] for task in run["tasks"]]
    if task_id is not None and task_id not in task_ids:
        raise HarnessError("Feedback task is outside the approved current Phase.")
    if run["stage"] not in {"technically_complete", "awaiting_acceptance", "failed", "stopped"}:
        raise HarnessError("Feedback requires a settled result; finish or inspect the current execution first.")
    index = None
    if kind == "defect":
        if run["stage"] in {"failed", "stopped"} and execution.get("stop_kind") not in {
                "code", "final_code", "correction_limit"}:
            raise HarnessError("Environment, permission or unknown failures cannot be relabeled as code defects.")
        index = task_ids.index(task_id)
        completed = execution.get("completed_tasks", [])
        if (completed != task_ids[:len(completed)] or task_id not in execution.get("task_states", {}) or
                index > execution.get("task_index", -1) or
                not set(run["tasks"][index]["depends_on"]) <= set(task_ids[:index]) or
                index > len(completed)):
            raise HarnessError("Defect feedback cannot reopen an unstarted or unordered Task.")
    feedback_id = feedback_id or "feedback-" + digest({**payload, "plan_hash": run["plan_hash"],
        "content_version": run["content_version"], "sequence": execution["sequence"],
        "final_validation_ids": execution.get("final_validation_ids", [])})[:24]
    detail = {"id": feedback_id, **payload, "phase_id": run["phase_id"], "plan_hash": run["plan_hash"],
              "policy_hash": run["policy_hash"], "content_version": run["content_version"],
              "sequence": execution["sequence"]}

    def route(current):
        if (current["content_version"] != detail["content_version"] or
                current["plan_hash"] != detail["plan_hash"] or
                current["policy_hash"] != detail["policy_hash"] or
                current["execution"]["sequence"] != detail["sequence"]):
            raise HarnessError("Execution changed before feedback could be recorded.")
        state = current["execution"]
        now = time.time()
        outcome = ("replanning_required" if kind == "requirements" else
                   "correction_limit" if state["corrections"][task_id] >= current["policy"]["max_corrections"] else
                   "correction_requested")
        record = {**detail, "received_at": now, "routing_outcome": outcome, "outcome": outcome,
                  "previous_completion": _previous_completion(current),
                  "history": [{"outcome": outcome, "at": now, "content_version": current["content_version"]}]}
        current.setdefault("feedback", []).append(record)
        for wait in current.get("waits", []):
            if wait.get("reason") == "result_acceptance" and wait.get("ended") is None:
                started = wait.get("started")
                wait.update(ended=now, duration=now - started if started is not None and now >= started else None)
        if outcome == "correction_limit":
            current.update(stage="failed", reason="Feedback retained; correction limit reached for " + task_id + ".")
            state.update(stop_kind="correction_limit", in_flight=False, active_step=None, ended=now)
        elif kind == "requirements":
            current.update(stage="replanning_required",
                           reason="Changed requirements require a revised plan and new execution approval.")
            current["replanning_feedback_id"] = feedback_id
            state.update(stop_kind="requirements_changed", in_flight=False, active_step=None, ended=now)
            # Original authorization remains historical evidence; the stage
            # invalidates execution until root creates and approves a new plan.
        else:
            old_completed = list(state["completed_tasks"])
            state["feedback_rechecks"] = [identity for identity in task_ids[index + 1:] if identity in old_completed]
            state["completed_tasks"] = task_ids[:index]
            state["task_index"] = index
            state["corrections"][task_id] += 1
            state["task_states"][task_id].update(validation_ids=[], feedback={
                "reason": "User reported a defect within the approved Task scope.",
                "evidence": [{"feedback_id": feedback_id, "text": text, "task_id": task_id,
                              "requirements": copy.deepcopy(current["tasks"][index]["requirements"])}]})
            state.update(stage="developer", in_flight=False, active_step=None, patch_pending=None,
                         final_validation_ids=[], stop_kind=None, ended=None)
            state.pop("final_content_version", None)
            current.update(stage="executing", reason=None)
            current.pop("acceptance", None)
        state["sequence"] += 1

    return workflow.store.transition(run["id"], run["id"] + ":feedback:" + feedback_id,
                                     "workflow_feedback_routed", detail, route)


def complete_feedback(current):
    """Mark routed defects corrected inside the final technical-completion transaction."""
    if current.get("stage") != "technically_complete":
        raise HarnessError("Feedback resolution requires technical completion.")
    execution = current["execution"]
    attempts = {item["id"]: effective_attempt(item) for item in current["attempts"]}
    task_ids = [task["id"] for task in current["tasks"]]
    if (execution.get("final_content_version") != current["content_version"] or
            not execution.get("final_validation_ids") or execution.get("completed_tasks") != task_ids):
        raise HarnessError("Feedback resolution requires final content and complete validation evidence.")
    for feedback in current.get("feedback", []):
        if feedback.get("outcome") != "correction_requested":
            continue
        state = execution["task_states"][feedback["task_id"]]
        reviewer = attempts.get(state.get("reviewer_attempt_id"), {})
        if (reviewer.get("id") in feedback["previous_completion"]["attempt_ids"] or
                reviewer.get("role") != "reviewer" or reviewer.get("task_id") != feedback["task_id"] or
                reviewer.get("outcome") != "validated" or reviewer.get("review_verdict") != "pass" or
                "finished" not in reviewer.get("journal_phases", {}) or not reviewer.get("findings_ingested") or
                reviewer.get("content_version") != state.get("completed_content_version")):
            raise HarnessError("Feedback resolution requires a subsequent independent Reviewer.")
        resolution = {"content_version": current["content_version"],
                      "final_validation_ids": copy.deepcopy(execution["final_validation_ids"]),
                      "reviewer_attempt_id": state["reviewer_attempt_id"], "at": time.time()}
        feedback.update(outcome="corrected", resolution=resolution)
        feedback["history"].append({"outcome": "corrected", **resolution})
