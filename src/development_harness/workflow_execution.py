"""Sequential real roles, bounded corrections and final-content validation.

Each completed boundary is durable. Explicit recovery verifies interrupted work;
result feedback reopens only the approved correction and validation sequence.
"""

import sqlite3
import time
from contextlib import nullcontext

from .files import require_snapshot
from .model import HarnessError, digest, file_digest
from .processes import ProjectLock
from .worker_contract import apply_proposal
from .workflow_records import WorkflowRecords


class Execution:
    def __init__(self, workflow, worker_factory, validator_factory, codex_path):
        self.workflow, self.store = workflow, workflow.store
        self.worker_factory, self.validator_factory, self.codex_path = worker_factory, validator_factory, codex_path
        self.validator = None

    def change(self, kind, detail, update):
        run = self.workflow.get()
        sequence = run["execution"]["sequence"]
        def apply(current):
            if current["execution"]["sequence"] != sequence:
                raise HarnessError("Execution journal changed unexpectedly.")
            update(current)
            current["execution"]["sequence"] += 1
        return self.store.transition(run["id"], run["id"] + ":execution:" + str(sequence), kind, detail, apply)

    def stop(self, kind, reason, *, failed=False):
        def stopped(run):
            run.update(stage="failed" if failed else "stopped", reason=reason)
            run["execution"].update(stop_kind=kind, in_flight=False, ended=time.time())
        return self.change("workflow_stopped", {"kind": kind, "reason": reason}, stopped)

    def boundary(self, stage, update=lambda _: None):
        def completed(run):
            update(run)
            run["execution"].update(stage=stage, in_flight=False, active_step=None)
            run["reason"] = None
        return self.change("execution_boundary", {"next_stage": stage}, completed)

    def correction(self, task_id, reason, evidence):
        run = self.workflow.get()
        used = run["execution"]["corrections"][task_id]
        if used >= run["policy"]["max_corrections"]:
            return self.stop("correction_limit", "Correction limit reached for " + task_id + ": " + reason, failed=True)
        def correct(current):
            state = current["execution"]
            state["corrections"][task_id] += 1
            state["task_states"][task_id]["feedback"] = {"reason": reason, "evidence": evidence}
            state["task_states"][task_id]["validation_ids"] = []
            state.update(stage="developer", in_flight=False, active_step=None)
            current["reason"] = None
        return self.change("correction_requested", {"task_id": task_id, "reason": reason, "evidence": evidence}, correct)

    def validation_factory(self, directory):
        if self.validator is None:
            self.validator = self.validator_factory(directory)
        return self.validator

    def step(self):
        run = self.workflow.get()
        state = run["execution"]
        stage = state["stage"]
        task = run["tasks"][min(state["task_index"], len(run["tasks"]) - 1)]
        task_id = task["id"]
        if not set(task["depends_on"]) <= set(state["completed_tasks"]):
            raise HarnessError("A task cannot start before all approved dependencies complete.")
        if stage == "developer" and task_id not in state["task_states"]:
            scope = self.workflow._scope(run, task_id)
            before = scope.packet()["files"]
            def start(current):
                current["execution"]["task_states"][task_id] = {
                    "before": before, "before_content_version": run["content_version"],
                    "validation_ids": [], "developer_attempt_id": None, "reviewer_attempt_id": None,
                    "feedback": None}
            self.change("task_started", {"task_id": task_id, "content_version": run["content_version"]}, start)
        def starting(current):
            current["execution"].update(in_flight=True, active_step={
                "id": str(current["execution"]["sequence"]), "stage": stage, "task_id": task_id,
                "before_attempt_ids": [item["id"] for item in current["attempts"]]})
        self.change("execution_step_started", {"stage": stage, "task_id": task_id}, starting)
        if stage == "developer":
            self.develop(task_id)
        elif stage == "validation":
            self.validate(task_id)
        elif stage == "review":
            self.review(task_id)
        elif stage == "final_validation":
            self.validate(task_id, final=True)
        else:
            raise HarnessError("Unknown execution boundary: " + stage)

    def develop(self, task_id):
        run = self.workflow.get()
        feedback = run["execution"]["task_states"][task_id]["feedback"]
        result = self.workflow._invoke(task_id, "developer", feedback=feedback,
                                       worker_factory=self.worker_factory, codex_path=self.codex_path)
        return self.apply_developer(task_id, result)

    def apply_developer(self, task_id, result):
        if result["response"]["status"] == "blocked":
            return self.stop("specification", "Developer needs clarification: " + "; ".join(result["response"]["questions"]))
        attempt_id = result["attempt"]["id"]
        run = self.workflow.get()
        scope = self.workflow._scope(run, task_id)
        if digest(scope.baseline) != result["attempt"]["content_version"]:
            raise HarnessError("Developer proposal belongs to a different content version.")
        patch_path = self.store.directory / "workflow" / run["id"] / ("patch-" + attempt_id)
        def applying(current):
            current["execution"]["patch_pending"] = {"task_id": task_id, "attempt_id": attempt_id,
                                                     "before": run["content_version"], "directory": str(patch_path)}
        self.change("patch_application_started", {"task_id": task_id, "attempt_id": attempt_id,
                    "proposal_hash": digest(result["response"])}, applying)
        applied = apply_proposal(scope, result["response"], patch_path)
        if applied["outcome"] != "applied":
            raise HarnessError("Partial file application requires inspection before further execution.")
        require_snapshot(self.workflow.project, applied["after"])
        return self.commit_patch(task_id, attempt_id, patch_path, applied)

    def commit_patch(self, task_id, attempt_id, patch_path, applied):
        def committed(current):
            current["expected"] = applied["after"]
            current["content_version"] = applied["content_version"]
            state = current["execution"]
            state["patches"].append({"task_id": task_id, "attempt_id": attempt_id,
                "before": digest(applied["before"]), "after": applied["content_version"],
                "record": str(patch_path / "patch.json"), "record_hash": file_digest(patch_path / "patch.json")})
            state["patch_pending"] = None
            state["task_states"][task_id].update(developer_attempt_id=attempt_id, validation_ids=[])
        self.boundary("validation", committed)
        self.workflow._check(self.workflow.get())

    def validate(self, task_id, *, final=False):
        run = self.workflow.get()
        evidence = []
        for index in range(len(run["policy"]["validation"])):
            result = self.workflow._validate_task(task_id, index, validator_factory=self.validation_factory)
            evidence.append(result)
            def record(current):
                if final:
                    current["execution"]["final_validation_ids"] = [item["id"] for item in evidence]
                else:
                    current["execution"]["task_states"][task_id]["validation_ids"] = [item["id"] for item in evidence]
            self.change("validation_result_recorded", {"attempt_id": result["id"], "final": final}, record)
            if result["outcome"] != "passed":
                kind = result.get("failure_kind") or ("code" if result["outcome"] == "failed" else
                                                       "interrupted" if result["outcome"] == "interrupted" else "validation_incomplete")
                reason = result.get("reason") or ("Required validation " + result["outcome"])
                if final:
                    return self.stop("final_" + kind, "Final Phase validation did not pass: " + reason,
                                     failed=kind == "code")
                if kind == "code":
                    from .isolated_validation import review_evidence
                    return self.correction(task_id, reason, [review_evidence(item) for item in evidence])
                return self.stop(kind, reason)
        if not final:
            return self.boundary("review")
        current = self.workflow.get()
        if WorkflowRecords(self.store, current["id"]).summary()["blocking_findings"]:
            return self.stop("mandatory_findings", "Mandatory review findings remain unresolved.")
        if current["execution"]["completed_tasks"] != [task["id"] for task in current["tasks"]]:
            raise HarnessError("Not all approved tasks have completed.")
        expected_checks = {digest(check) for check in current["policy"]["validation"]}
        if ({item["check_hash"] for item in evidence} != expected_checks or
                any(item["content_version"] != current["content_version"] or item["plan_hash"] != current["plan_hash"]
                    or item["outcome"] != "passed" for item in evidence)):
            raise HarnessError("Final validation evidence does not match the final plan/code version.")
        def complete(value):
            value.update(stage="technically_complete", reason=None)
            value["execution"].update(stage="complete", in_flight=False, active_step=None, ended=time.time(),
                                       final_content_version=value["content_version"])
            from .workflow_acceptance import completion_id
            from .workflow_feedback import complete_feedback
            complete_feedback(value)
            value["waits"].append({"id": value["id"] + ":acceptance:" + completion_id(value),
                                  "reason": "result_acceptance", "started": time.time(), "ended": None, "duration": None})
        self.change("workflow_technically_complete", {"content_version": current["content_version"],
                    "validation_ids": [item["id"] for item in evidence]}, complete)

    def review(self, task_id):
        result = self.workflow._invoke(task_id, "reviewer", worker_factory=self.worker_factory,
                                       codex_path=self.codex_path)
        return self.review_result(task_id, result)

    def review_result(self, task_id, result):
        response = result["response"]
        run = self.workflow.get()
        task_findings = [item for item in run["findings"].values() if item["task_id"] == task_id]
        if response["verdict"] == "blocked":
            return self.stop("specification", "Reviewer needs clarification: " + "; ".join(response["questions"]))
        mandatory = [item for item in task_findings if item["required"] and item["status"] in {"open", "deferred"}]
        if mandatory or response["verdict"] != "pass":
            details = [{key: item[key] for key in ("id", "requirement_id", "path", "severity", "status", "evidence", "recommendation")}
                       for item in mandatory]
            return self.correction(task_id, "Mandatory review changes remain.", details)
        def accepted(current):
            state = current["execution"]
            state["task_states"][task_id].update(reviewer_attempt_id=result["attempt"]["id"],
                                                  completed_content_version=current["content_version"])
            state["completed_tasks"].append(task_id)
            state["task_index"] += 1
            if task_id in state.get("feedback_rechecks", []):
                state["feedback_rechecks"].remove(task_id)
            if state["task_index"] < len(current["tasks"]):
                next_task = current["tasks"][state["task_index"]]["id"]
                if next_task in state.get("feedback_rechecks", []):
                    state["task_states"][next_task]["validation_ids"] = []
        next_index = run["execution"]["task_index"] + 1
        next_stage = ("final_validation" if next_index == len(run["tasks"]) else
                      "validation" if run["tasks"][next_index]["id"] in run["execution"].get("feedback_rechecks", []) else "developer")
        self.boundary(next_stage, accepted)


def execute(workflow, *, worker_factory, validator_factory, codex_path=None, steps=None, _locked=False):
    if steps is not None and (type(steps) is not int or steps < 1):
        raise HarnessError("steps must be a positive integer.")
    with nullcontext() if _locked else ProjectLock(workflow.store):
        run = workflow.get()
        workflow._check(run)
        if run["policy"].get("workflow_version") != 1 or "initial_expected" not in run:
            raise HarnessError("Prepare and authorize a workflow with the current execution policy first.")
        if not run["approval"] or run["stage"] == "awaiting_execution_approval":
            raise HarnessError("Explicit execution approval is required before workflow-run.")
        if run["stage"] in {"cancelled", "failed", "stopped", "technically_complete", "accepted", "superseded", "replanning_required"}:
            return run
        if "execution" not in run:
            if run["attempts"]:
                raise HarnessError("Standalone attempts exist; prepare a fresh workflow before sequential execution.")
            def initialize(current):
                current["stage"] = "executing"
                current["execution"] = {"sequence": 0, "task_index": 0, "stage": "developer",
                    "corrections": {task["id"]: 0 for task in current["tasks"]}, "completed_tasks": [],
                    "task_states": {}, "final_validation_ids": [], "patches": [], "patch_pending": None,
                    "in_flight": False, "stop_kind": None, "started": time.time(), "ended": None}
            run = workflow.store.transition(run["id"], run["id"] + ":execution-started", "execution_started", {}, initialize)
        engine = Execution(workflow, worker_factory, validator_factory, codex_path)
        if run["execution"]["in_flight"] or run["execution"]["patch_pending"] or workflow._pending(run):
            return engine.stop("interrupted", "Previous execution boundary is incomplete; inspection and T5 recovery are required.")
        count = 0
        try:
            while workflow.get()["stage"] == "executing":
                workflow._check(workflow.get())
                engine.step()
                count += 1
                if steps is not None and count >= steps:
                    break
        except KeyboardInterrupt:
            engine.stop("interrupted", "Execution interrupted; partial files and evidence are preserved.")
        except (HarnessError, OSError, sqlite3.Error) as exc:
            kind = "permission" if isinstance(exc, PermissionError) else "execution_error"
            engine.stop(kind, str(exc))
        return workflow.get()
