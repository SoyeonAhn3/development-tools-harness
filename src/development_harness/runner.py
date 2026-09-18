"""Small sequential state machine; the only AI implementation here is synthetic."""

import copy
import hashlib
from pathlib import Path
import time
import uuid

from .files import apply_write, differences, require_snapshot, snapshot, target
from .model import HarnessError, digest, file_digest, load_plan
from .processes import ProjectLock, alive
from .store import Store
from .validation import validate


class Harness:
    def __init__(self, project, home=None):
        self.store = Store(project, home)
        self.project = self.store.project

    def _execution_run(self):
        run = self.store.get()
        if run.get("kind") == "planning":
            raise HarnessError("This is a planning-only run. Use plan-status/plan-approve/plan-cancel; real implementation is Phase 3.")
        return run

    def prepare(self, plan_path):
        with ProjectLock(self.store):
            if self.store.active():
                raise HarnessError("An unfinished run exists. Inspect, resume or explicitly cancel it first.")
            plan_path = Path(plan_path).resolve()
            plan, plan_hash = load_plan(plan_path)
            for task in plan["tasks"]:
                for writes in task["writes"]:
                    for name in writes:
                        if target(self.project, name) == plan_path:
                            raise HarnessError("A task cannot modify its own approved plan.")
            baseline = snapshot(self.project)
            names = {name.casefold(): name for name in baseline}
            for task in plan["tasks"]:
                for writes in task["writes"]:
                    for name in writes:
                        folded = name.casefold()
                        if folded in names and names[folded] != name:
                            raise HarnessError(f"Write path casing differs from another project/plan path: {name}")
                        names[folded] = name
            run = {
                "id": uuid.uuid4().hex, "project_id": self.store.project_id, "phase_id": plan["phase"],
                "project": str(self.project), "plan_path": str(plan_path), "plan_hash": plan_hash,
                "plan": plan, "baseline": baseline, "expected": baseline, "approval": None,
                "stage": "awaiting_approval", "task_index": 0, "corrections": 0,
                "attempts": [], "completed_tasks": [], "findings": {}, "journal": None,
                "reason": None, "created": time.time(), "waiting_since": time.time(),
                "approval_wait_seconds": 0, "synthetic": True,
            }
            self.store.save(run, "prepared", {"input_hash": digest(baseline)}, new=True)
            return run

    def _check(self, run, *, partial=False):
        try:
            current_hash = file_digest(run["plan_path"])
        except OSError as exc:
            raise HarnessError("Approved plan is unavailable; restore it or cancel and prepare a new run.") from exc
        if current_hash != run["plan_hash"]:
            raise HarnessError("Plan changed; prior approval cannot authorize it. Restore it or cancel and prepare a new run.")
        for attempt in run["attempts"]:
            if attempt["outcome"] in {"running", "launching"} and alive(attempt.get("process")):
                raise HarnessError("A recorded validation worker is still active; wait for it to exit before resuming.")
        if partial and run["journal"]:
            journal = run["journal"]
            actual = snapshot(self.project)
            names = actual.keys() | journal["before"].keys() | journal["after"].keys()
            unexpected = [name for name in names if actual.get(name) not in
                          (journal["before"].get(name), journal["after"].get(name))]
            if unexpected:
                raise HarnessError("Partial work or user edits require inspection; preserved: " + ", ".join(sorted(unexpected)))
        else:
            require_snapshot(self.project, run["expected"])
        if run["approval"] and (run["approval"]["plan_hash"] != run["plan_hash"] or
                                run["approval"]["input_hash"] != digest(run["baseline"])):
            raise HarnessError("Approval does not match the recorded plan/input version.")

    def approve(self):
        with ProjectLock(self.store):
            run = self._execution_run()
            self._check(run)
            if run["approval"]:
                return run
            if run["stage"] != "awaiting_approval":
                raise HarnessError("This run is not waiting for plan approval.")
            run["approval"] = {"plan_hash": run["plan_hash"], "input_hash": digest(run["baseline"]), "at": time.time()}
            self._finish_wait(run)
            run["stage"] = "implementing"
            self.store.save(run, "plan_approved", run["approval"])
            return run

    @staticmethod
    def _finish_wait(run):
        if run["waiting_since"] is not None:
            run["approval_wait_seconds"] += time.time() - run["waiting_since"]
            run["waiting_since"] = None

    def cancel(self):
        with ProjectLock(self.store):
            run = self._execution_run()
            for attempt in run["attempts"]:
                if alive(attempt.get("process")) and attempt["outcome"] in {"running", "launching"}:
                    raise HarnessError("A validation worker is still active; cannot cancel yet.")
            if run["stage"] == "accepted":
                raise HarnessError("An accepted result cannot be cancelled.")
            self._finish_wait(run)
            run["stage"] = "cancelled"
            run["reason"] = "Explicitly cancelled; files and evidence preserved."
            self.store.save(run, "cancelled")
            return run

    def accept(self):
        with ProjectLock(self.store):
            run = self._execution_run()
            self._check(run)
            if run["stage"] != "awaiting_acceptance":
                raise HarnessError("Required work is not complete; result acceptance is unavailable.")
            if any(item["status"] != "resolved" for item in run["findings"].values()):
                raise HarnessError("Mandatory review findings remain unresolved.")
            final = run.get("final_evidence", [])
            if len(final) != len(run["plan"]["validation"]) or any(
                evidence["outcome"] != "passed" or evidence["code_hash"] != digest(run["expected"])
                or evidence["plan_hash"] != run["plan_hash"] for evidence in final
            ):
                raise HarnessError("Final verification evidence is missing or obsolete.")
            self._finish_wait(run)
            run["stage"] = "accepted"
            run["accepted"] = {"at": time.time(), "code_hash": digest(run["expected"]), "plan_hash": run["plan_hash"]}
            self.store.save(run, "result_accepted", run["accepted"])
            return run

    def execute(self, steps=None):
        with ProjectLock(self.store):
            run = self._execution_run()
            if run["stage"] in {"accepted", "cancelled", "failed", "awaiting_approval", "awaiting_acceptance"}:
                return run
            if not run["approval"]:
                raise HarnessError("Implementation requires explicit plan approval.")
            try:
                self._check(run, partial=run["stage"] == "implementing")
                for attempt in run["attempts"]:
                    if attempt["outcome"] in {"running", "launching"}:
                        # A launching worker receives no command before its identity is persisted.
                        attempt.update(outcome="interrupted", ended=None, duration=None,
                                       reason="Previous invocation ended without a confirmed result.")
                run["reason"] = None
                self.store.save(run, "execution_started")
                count = 0
                while run["stage"] not in {"awaiting_acceptance", "failed"}:
                    self._check(run, partial=run["stage"] == "implementing")
                    stage = run["stage"]
                    if stage == "implementing":
                        self._implement(run)
                    elif stage in {"validating", "final_validating"}:
                        if not self._validate(run):
                            break
                    elif stage == "reviewing":
                        self._review(run)
                    else:
                        raise HarnessError(f"Unknown execution stage: {stage}")
                    count += 1
                    if steps is not None and count >= steps:
                        self.store.save(run, "paused_at_boundary", {"next_stage": run["stage"]})
                        break
            except KeyboardInterrupt:
                for attempt in run["attempts"]:
                    if attempt["outcome"] in {"running", "launching"}:
                        attempt.update(outcome="interrupted", ended=None, duration=None,
                                       reason="Interrupted span; exact execution duration is unknown.")
                run["reason"] = "Interrupted by user; inspect status and resume."
                self.store.save(run, "interrupted")
            except (HarnessError, OSError) as exc:
                run["reason"] = str(exc)
                self.store.save(run, "stopped", {"reason": str(exc)})
                raise HarnessError(str(exc)) from exc
            return run

    def _attempt(self, run, role):
        item = {"id": uuid.uuid4().hex, "role": role, "synthetic": role != "validation",
                "task_id": run["plan"]["tasks"][run["task_index"]]["id"],
                "stage": run["stage"], "correction": run["corrections"],
                "plan_hash": run["plan_hash"], "code_hash": digest(run["expected"]),
                "started": time.time(), "ended": None, "duration": None, "outcome": "running"}
        run["attempts"].append(item)
        return item

    def _implement(self, run):
        task = run["plan"]["tasks"][run["task_index"]]
        writes = task["writes"][min(run["corrections"], len(task["writes"]) - 1)]
        if run["journal"] is None:
            before = copy.deepcopy(run["expected"])
            after = {**before, **{name: hashlib.sha256(text.encode()).hexdigest() for name, text in writes.items()}}
            attempt = self._attempt(run, "developer")
            run["journal"] = {"before": before, "after": after, "attempt_id": attempt["id"]}
            self.store.save(run, "implementation_started", {"attempt_id": attempt["id"]})
        else:
            attempt = next(a for a in run["attempts"] if a["id"] == run["journal"]["attempt_id"])
        journal = run["journal"]
        actual = snapshot(self.project)
        for name, content in writes.items():
            if actual.get(name) == journal["after"].get(name):
                continue
            self._check(run, partial=True)
            apply_write(self.project, name, content, journal["before"].get(name))
        require_snapshot(self.project, journal["after"])
        run["expected"] = journal["after"]
        run["journal"] = None
        attempt.update(outcome="passed", ended=time.time(), code_hash=digest(run["expected"]))
        # A recovered interrupted span has no exact execution duration.
        attempt["duration"] = None if attempt.get("reason") else attempt["ended"] - attempt["started"]
        run["stage"] = "validating"
        self.store.save(run, "implementation_finished", {"attempt_id": attempt["id"]})

    def _correct(self, run, reason):
        run["reason"] = reason
        if run["corrections"] >= run["plan"]["max_corrections"]:
            run["stage"] = "failed"
            run["reason"] = "Correction limit reached: " + reason
        else:
            run["corrections"] += 1
            run["stage"] = "implementing"
        self.store.save(run, "correction_decided", {"reason": run["reason"]})

    def _validate(self, run):
        final = run["stage"] == "final_validating"
        batch = []
        for check in run["plan"]["validation"]:
            self._check(run)
            attempt = self._attempt(run, "validation")
            attempt["outcome"] = "launching"
            self.store.save(run, "validation_started", {"attempt_id": attempt["id"]})
            validate(check, self.project, self.store.directory, attempt,
                     lambda value: self.store.save(run, "worker_registered", {"attempt_id": value["id"]}))
            try:
                require_snapshot(self.project, run["expected"])
            except HarnessError:
                attempt["outcome"] = "unverified"
                self.store.save(run, "validation_content_changed", {"attempt_id": attempt["id"]})
                raise
            self.store.save(run, "validation_finished", {"attempt_id": attempt["id"], "outcome": attempt["outcome"]})
            batch.append(copy.deepcopy(attempt))
            if attempt["outcome"] == "failed":
                self._correct(run, "Required validation failed.")
                return True
            if attempt["outcome"] != "passed":
                run["reason"] = attempt.get("reason", "Required check did not pass: " + attempt["outcome"])
                self.store.save(run, "validation_stopped", {"reason": run["reason"]})
                return False
        if final:
            run["final_evidence"] = batch
            run["stage"] = "awaiting_acceptance"
            run["waiting_since"] = time.time()
        else:
            run["task_evidence"] = batch
            run["stage"] = "reviewing"
        run["reason"] = None
        self.store.save(run, "validation_batch_passed")
        return True

    def _review(self, run):
        task = run["plan"]["tasks"][run["task_index"]]
        evidence = run.get("task_evidence", [])
        if not evidence or any(item["outcome"] != "passed" or item["code_hash"] != digest(run["expected"]) for item in evidence):
            raise HarnessError("Review requires validation of the current code.")
        attempt = self._attempt(run, "reviewer")
        outcome = task["review"][min(run["corrections"], len(task["review"]) - 1)]
        attempt.update(outcome=outcome, ended=time.time())
        attempt["duration"] = attempt["ended"] - attempt["started"]
        key = task["id"] + ":required-change"
        if outcome == "changes":
            run["findings"][key] = {"status": "open", "mandatory": True, "synthetic": True,
                                    "review_id": attempt["id"], "message": "Fake Reviewer requests a required correction."}
            self._correct(run, "Mandatory fake-review finding remains open.")
        else:
            if key in run["findings"]:
                run["findings"][key].update(status="resolved", review_id=attempt["id"],
                                            validation_ids=[item["id"] for item in evidence])
            run["completed_tasks"] = [item for item in run["completed_tasks"] if item["id"] != task["id"]]
            run["completed_tasks"].append({"id": task["id"], "code_hash": digest(run["expected"]), "review_id": attempt["id"]})
            if run["task_index"] + 1 < len(run["plan"]["tasks"]):
                run["task_index"] += 1
                run["corrections"] = 0
                run["stage"] = "implementing"
            else:
                run["stage"] = "final_validating"
            self.store.save(run, "review_passed", {"attempt_id": attempt["id"]})

    def status(self):
        run = self._execution_run()
        result = {key: run[key] for key in ("id", "project_id", "phase_id", "stage", "task_index", "corrections", "reason")}
        result.update(plan_hash=run["plan_hash"], code_hash=digest(run["expected"]),
                      approval=run["approval"], database=str(self.store.path),
                      attempts=run["attempts"], findings=run["findings"],
                      completed_tasks=run["completed_tasks"], synthetic=True, actual_ai_calls=0,
                      approval_wait_seconds=run["approval_wait_seconds"])
        try:
            result["changed_files"] = differences(run["expected"], snapshot(self.project))
            result["plan_changed"] = file_digest(run["plan_path"]) != run["plan_hash"]
        except (OSError, HarnessError) as exc:
            result["inspection_error"] = str(exc)
        return result
