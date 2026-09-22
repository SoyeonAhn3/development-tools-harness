"""Version-bound admission and controlled real workflow execution for Phase 3."""

import copy
import hashlib
import json
from pathlib import Path
import time
import uuid

from .files import require_snapshot, snapshot, target
from .isolated_validation import IsolatedValidator, pytest_arguments, review_evidence
from .model import HarnessError, digest
from .phase_docs import validate_profile
from .plan_schema import validate_plan
from .planning import Planning
from .processes import ProjectLock, alive
from .project import OUTPUT, load_project
from .store import Store
from .worker_contract import TaskScope, REVIEWER_FOLLOWUP_SCHEMA
from .workers import CodexWorker, INSTRUCTIONS, REVIEWER_FOLLOWUP_INSTRUCTIONS
from .workflow_records import WorkflowRecords, effective_attempt, reconciled_retry


class Workflow:
    def __init__(self, project, home=None):
        self.store = Store(project, home)
        self.project = self.store.project

    def get(self):
        return self.store.latest("workflow")

    def _source(self, source_id=None):
        latest = self.store.latest("planning")
        source = self.store.get(source_id) if source_id else latest
        if source.get("kind") != "planning" or source["id"] != latest["id"]:
            raise HarnessError("Only the latest planning run can authorize a workflow.")
        with self.store.connect() as db:
            histories = [json.loads(row[0]) for row in db.execute("SELECT data FROM runs")]
        if any(item.get("kind") == "workflow" and item.get("planning_run_id") == source["id"] and
               any(feedback.get("kind") == "requirements" for feedback in item.get("feedback", []))
               for item in histories):
            raise HarnessError("Requirements feedback invalidated this planning version; start revised planning.")
        if source["stage"] != "plan_approved" or not source.get("approval") or not source.get("versions"):
            raise HarnessError("An approved planning version is required before workflow preparation.")
        version, approval = source["versions"][-1], source["approval"]
        if (approval.get("scope") != "planning_only" or approval.get("version") != version["version"] or
                approval.get("plan_hash") != version["plan_hash"] or digest(version["plan"]) != version["plan_hash"] or
                approval.get("input_hash") != source["input_hash"] or version["input_hash"] != source["input_hash"] or
                digest(source["baseline"]) != source["input_hash"]):
            raise HarnessError("Planning approval does not match the recorded plan/input version.")
        if "writing_profile" in source:
            validate_profile(source["writing_profile"])
            profile_hash = source["writing_profile"]["sha256"]
            if any(record.get("writing_profile_hash") != profile_hash for record in (version, approval)):
                raise HarnessError("Planning approval does not match the pinned writing profile.")
        Planning(self.project, self.store.home)._artifacts(source)
        return source, version

    def _scope(self, run, task_id):
        task = next((item for item in run["tasks"] if item["id"] == task_id), None)
        if task is None:
            raise HarnessError("Task is outside the admitted current Phase.")
        if any(path.casefold() == run["config"]["spec"].casefold() for path in task["paths"]):
            raise HarnessError("Implementation cannot change the registered specification.")
        requirements = {item["id"]: item["text"]["en"] + "\n" + item["text"]["ko"]
                        for item in run["plan"]["requirements"] if item["id"] in task["requirements"]}
        context = list(dict.fromkeys([run["config"]["spec"], *run["config"]["context"],
                                     *(item["path"] for item in run["plan"]["code_context"])]))
        instructions = json.dumps({key: task[key] for key in ("title", "acceptance", "verification", "depends_on")},
                                  ensure_ascii=False)
        return TaskScope(self.project, task_id, requirements, task["paths"], context, instructions=instructions)

    def prepare(self, planning_run_id=None, *, max_corrections=None, manual_checks=None):
        with ProjectLock(self.store):
            if max_corrections is not None and (type(max_corrections) is not int or not 0 <= max_corrections <= 100):
                raise HarnessError("max_corrections must be an integer from 0 to 100.")
            source, version = self._source(planning_run_id)
            active = self.store.active()
            if active:
                if active.get("kind") == "workflow" and active["planning_run_id"] == source["id"]:
                    self._check(active)
                    if max_corrections is not None and max_corrections != active["policy"]["max_corrections"]:
                        raise HarnessError("Correction limit is pinned; cancel and prepare a new execution policy.")
                    if manual_checks is not None and manual_checks != active["policy"].get("manual_checks", []):
                        raise HarnessError("Manual checks are pinned; prepare and approve a new execution policy.")
                    return active
                raise HarnessError("An unfinished run exists; inspect or explicitly cancel it first.")
            planner = Planning(self.project, self.store.home)
            files = planner._check(source)
            planner._require_evidence(source)
            plan = copy.deepcopy(version["plan"])
            validate_plan(plan, files, skill="writing_profile" in source)
            from .workflow_acceptance import validate_manual_checks
            manual_checks = validate_manual_checks([] if manual_checks is None else manual_checks, plan)
            if any(item["blocking"] for item in plan["questions"]):
                raise HarnessError("Blocking planning questions prevent execution admission.")
            config = copy.deepcopy(source["config"])
            for check in config["validation"]:
                pytest_arguments(check)
            policy = {"validation": config["validation"], "max_corrections": 2 if max_corrections is None else max_corrections,
                      "worker_boundary": "text-only-v1", "role_instructions_hash": digest(INSTRUCTIONS),
                      "validation_backend": "appcontainer", "workflow_version": 1,
                      "result_version": 1, "manual_checks": manual_checks,
                      "review_followup_hash": digest({"schema": REVIEWER_FOLLOWUP_SCHEMA,
                                                     "instructions": REVIEWER_FOLLOWUP_INSTRUCTIONS})}
            now, run_id = time.time(), uuid.uuid4().hex
            expected = snapshot(self.project)
            run = {"id": run_id, "kind": "workflow", "project_id": self.store.project_id,
                   "project": str(self.project), "phase_id": plan["current_phase"],
                   "planning_run_id": source["id"], "plan_version": version["version"],
                   "plan_hash": version["plan_hash"], "plan": plan, "tasks": plan["tasks"],
                   "planning_approval": copy.deepcopy(source["approval"]),
                   "writing_profile_hash": version.get("writing_profile_hash"),
                   "artifacts": copy.deepcopy(version["artifacts"]), "config": config,
                   "baseline": copy.deepcopy(source["baseline"]), "input_hash": source["input_hash"],
                   "initial_expected": copy.deepcopy(expected), "initial_content_version": digest(expected),
                   "expected": expected, "content_version": digest(expected),
                   "policy": policy, "policy_hash": digest(policy), "approval": None,
                   "stage": "awaiting_execution_approval", "created": now, "reason": None,
                   "attempts": [], "findings": {},
                   "waits": [{"id": run_id + ":execution", "reason": "execution_approval", "started": now,
                              "ended": None, "duration": None}]}
            for task in run["tasks"]:
                self._scope(run, task["id"])
            self._check(run)
            self.store.save(run, "workflow_prepared", {"planning_run_id": source["id"],
                            "plan_hash": run["plan_hash"], "content_version": run["content_version"]}, new=True)
            return run

    def _check(self, run, *, check_files=True):
        source, version = self._source(run["planning_run_id"])
        if (run["plan_version"] != version["version"] or run["plan_hash"] != version["plan_hash"] or
                digest(run["plan"]) != run["plan_hash"] or run["tasks"] != run["plan"]["tasks"] or
                run["planning_approval"] != source["approval"] or run["input_hash"] != source["input_hash"] or
                run["artifacts"] != version["artifacts"] or
                run["writing_profile_hash"] != version.get("writing_profile_hash") or
                digest(run["baseline"]) != run["input_hash"] or
                digest(run["expected"]) != run["content_version"]):
            raise HarnessError("Workflow references a stale or altered approved planning version.")
        initial = run.get("initial_expected", run["expected"])
        initial_version = run.get("initial_content_version", run["content_version"])
        if digest(initial) != initial_version:
            raise HarnessError("Initial content identity changed.")
        self._check_patches(run, initial)
        initial_inputs = {name: value for name, value in initial.items()
                          if not name.startswith(OUTPUT + "/")}
        if initial_inputs != source["baseline"]:
            raise HarnessError("Starting content differs from the approved planning baseline.")
        config, _ = load_project(self.project)
        if config != run["config"] or config != source["config"]:
            raise HarnessError("Registered validation/configuration changed; execution is blocked.")
        if (digest(run["policy"]) != run["policy_hash"] or run["policy"]["validation"] != config["validation"] or
                run["policy"]["role_instructions_hash"] != digest(INSTRUCTIONS)):
            raise HarnessError("Execution policy or role instructions changed.")
        if "review_followup_hash" in run["policy"] and run["policy"]["review_followup_hash"] != digest({
                "schema": REVIEWER_FOLLOWUP_SCHEMA, "instructions": REVIEWER_FOLLOWUP_INSTRUCTIONS}):
            raise HarnessError("Pinned follow-up review contract changed.")
        if check_files:
            require_snapshot(self.project, run["expected"])
        if run["approval"]:
            required = {"plan_hash": run["plan_hash"], "input_hash": run["input_hash"],
                        "content_version": initial_version, "policy_hash": run["policy_hash"],
                        "scope": "execution"}
            if any(run["approval"].get(key) != value for key, value in required.items()):
                raise HarnessError("Execution authorization does not match this plan, code and policy.")

    def _check_patches(self, run, initial):
        """Every accepted content change must trace to a recorded scoped proposal."""
        expected = dict(initial)
        attempts = {item["id"]: effective_attempt(item) for item in run["attempts"]}
        tasks = {item["id"]: item for item in run["tasks"]}
        for patch in run.get("execution", {}).get("patches", []):
            attempt = attempts.get(patch["attempt_id"], {})
            record_path = target(self.store.directory,
                                 "workflow/" + run["id"] + "/patch-" + patch["attempt_id"] + "/patch.json")
            if Path(patch["record"]) != record_path:
                raise HarnessError("Patch evidence is outside its recorded attempt directory.")
            raw = record_path.read_bytes()
            if hashlib.sha256(raw).hexdigest() != patch["record_hash"]:
                raise HarnessError("Applied patch evidence changed.")
            try:
                record = json.loads(raw)
                proposal = record["proposal"]
                if (patch["task_id"] not in tasks or record["task_id"] != patch["task_id"] or
                        patch["before"] != digest(expected) or record["before"] != expected or
                        record["outcome"] != "applied" or attempt.get("role") != "developer" or
                        attempt.get("task_id") != patch["task_id"] or attempt.get("outcome") != "validated" or
                        attempt.get("content_version") != patch["before"] or
                        attempt.get("response_hash") != digest(proposal)):
                    raise HarnessError("Applied patch does not match the recorded Developer proposal.")
                for change in proposal["changes"]:
                    if (change["path"] not in tasks[patch["task_id"]]["paths"] or
                            change["base_sha256"] != expected.get(change["path"], "absent")):
                        raise HarnessError("Applied patch is outside the approved Task or file version.")
                    expected[change["path"]] = hashlib.sha256(change["content"].encode("utf-8")).hexdigest()
                if (record["after"] != expected or record["content_version"] != digest(expected) or
                        patch["after"] != digest(expected)):
                    raise HarnessError("Applied patch content identity changed.")
            except (ValueError, KeyError, TypeError) as exc:
                raise HarnessError("Applied patch evidence is invalid.") from exc
        if expected != run["expected"]:
            raise HarnessError("Current content has no complete chain of recorded patches from the approved start.")

    def approve(self):
        with ProjectLock(self.store):
            run = self.get()
            self._check(run)
            if run["stage"] == "cancelled":
                raise HarnessError("A cancelled workflow cannot be approved.")
            if run["approval"]:
                return run
            if run["stage"] != "awaiting_execution_approval":
                raise HarnessError("Workflow is not awaiting execution approval.")
            def admit(current):
                now = time.time()
                current["approval"] = {"plan_hash": current["plan_hash"], "input_hash": current["input_hash"],
                                       "content_version": current["content_version"], "policy_hash": current["policy_hash"],
                                       "at": now, "scope": "execution"}
                current["stage"] = "execution_ready"
                for wait in current["waits"]:
                    if wait["ended"] is None:
                        wait["ended"] = now
                        wait["duration"] = now - wait["started"] if now >= wait["started"] else None
            return self.store.transition(run["id"], run["id"] + ":admitted", "execution_authorized",
                                         {"plan_hash": run["plan_hash"], "content_version": run["content_version"],
                                          "policy_hash": run["policy_hash"]}, admit)

    @staticmethod
    def _pending(run):
        return [item["id"] for raw in run["attempts"] if not reconciled_retry(raw)
                for item in [effective_attempt(raw)]
                if "finished" not in item.get("journal_phases", {}) or
                item.get("outcome") not in {"validated", "passed", "failed", "blocked"} or
                item.get("dispatch_status") == "uncertain" or
                (item["role"] == "reviewer" and item.get("outcome") == "validated" and
                 not item.get("findings_ingested"))]

    def invoke(self, task_id, role, **options):
        with ProjectLock(self.store):
            if self.get()["stage"] != "execution_ready":
                raise HarnessError("Single-role calls require execution authorization and an idle execution-ready workflow.")
            return self._invoke(task_id, role, **options)

    def _invoke(self, task_id, role, *, before=None, validation=None, feedback=None,
               worker_factory=CodexWorker, codex_path=None):
        """One role under the caller's project lock; the scheduler applies changes."""
        run = self.get()
        self._check(run)
        if run["stage"] not in {"execution_ready", "executing"} or not run["approval"]:
            raise HarnessError("Explicit execution authorization is required.")
        if self._pending(run):
            raise HarnessError("An incomplete or unverified attempt requires inspection; automatic redispatch is disabled.")
        if role not in {"developer", "reviewer"}:
            raise HarnessError("Unknown workflow AI role.")
        scope = self._scope(run, task_id)
        prior_findings = []
        if role == "reviewer":
            task_state = run.get("execution", {}).get("task_states", {}).get(task_id, {})
            recorded_before = task_state.get("before", scope.packet()["files"])
            if before is not None and before != recorded_before:
                raise HarnessError("Reviewer before-files must match the controller's recorded baseline.")
            before = recorded_before
            checks = {digest(check) for check in run["policy"]["validation"]}
            batch_ids = task_state.get("validation_ids")
            candidates = [effective_attempt(item) for item in run["attempts"] if item["role"] == "validation" and
                          item["task_id"] == task_id and item["content_version"] == digest(run["expected"]) and
                          (batch_ids is None or item["id"] in batch_ids)]
            by_check = {item["check_hash"]: item for item in candidates}
            if set(by_check) != checks or any(item.get("outcome") != "passed" for item in by_check.values()):
                raise HarnessError("Reviewer requires recorded passing evidence for every registered check.")
            recorded = [review_evidence(by_check[digest(check)]) for check in run["policy"]["validation"]]
            if validation is not None and validation != recorded:
                raise HarnessError("Reviewer evidence must match the controller's recorded validation.")
            validation = recorded
            prior_findings = [{key: item[key] for key in (
                "id", "task_id", "requirement_id", "path", "required", "status", "evidence", "recommendation", "severity")}
                for _, item in sorted(run["findings"].items())
                if item["task_id"] == task_id and item["status"] in {"open", "deferred"}]
        records = WorkflowRecords(self.store, run["id"])
        attempt = records.prepare_attempt(task_id, role, digest(scope.baseline))
        directory = self.store.directory / "workflow" / run["id"] / attempt["id"]
        selection = {"codex_path": codex_path} if codex_path is not None else {}
        worker = worker_factory(role, run["config"]["model"], directory, **selection)
        followup = {"prior_findings": prior_findings} if prior_findings else {}
        result = worker.invoke(scope, before=before, validation=validation, feedback=feedback,
                               attempt=attempt, lifecycle=records.lifecycle,
                               timeout=run["config"]["planner_timeout"], **followup)
        self._check(self.store.get(run["id"]))
        if any(item.get("session_id") == result["attempt"].get("session_id")
               for raw in run["attempts"] for item in [effective_attempt(raw)] if item.get("session_id")):
            raise HarnessError("A worker reused a previous session; independent review is unverified.")
        if role == "reviewer":
            if prior_findings:
                records.apply_review_assessments(attempt["id"], result["response"])
            else:
                records.ingest_findings(attempt["id"], result["response"]["findings"])
        return result

    def validate_task(self, task_id, check_index, **options):
        with ProjectLock(self.store):
            if self.get()["stage"] != "execution_ready":
                raise HarnessError("Single-check calls require execution authorization and an idle execution-ready workflow.")
            return self._validate_task(task_id, check_index, **options)

    def _validate_task(self, task_id, check_index, *, validator_factory=IsolatedValidator):
        """Record one registered isolated check under the caller's project lock."""
        run = self.get()
        self._check(run)
        if run["stage"] not in {"execution_ready", "executing"} or not run["approval"]:
            raise HarnessError("Explicit execution authorization is required.")
        if self._pending(run):
            raise HarnessError("An incomplete or unverified attempt requires inspection.")
        scope = self._scope(run, task_id)
        checks = run["policy"]["validation"]
        if type(check_index) is not int or not 0 <= check_index < len(checks):
            raise HarnessError("Select a registered validation check.")
        check = checks[check_index]
        records = WorkflowRecords(self.store, run["id"])
        attempt = records.prepare_attempt(task_id, "validation", digest(scope.baseline))
        attempt["check_hash"] = digest(check)
        records.lifecycle(attempt, "prepared")
        # Copied Python/pytest trees need room below Windows MAX_PATH. The
        # globally unique controller attempt and its record path retain linkage.
        directory = self.store.home / "workflow-validation" / attempt["id"]
        def launched(evidence):
            attempt.update(copy.deepcopy(evidence))
            records.lifecycle(attempt, "process_registered")
        try:
            validator = validator_factory(directory)
            if not getattr(validator, "policy", None) or not validator.policy.get("ready"):
                validator.verify()
            evidence = validator.run(check, self.project, launched=launched, attempt_id=attempt["id"])
            attempt.update(evidence)
            from .workflow_acceptance import seal_validation
            attempt["artifact_hashes"] = seal_validation(evidence)
            self._check(self.store.get(run["id"]))
        except BaseException as exc:
            attempt.update(outcome="interrupted" if isinstance(exc, KeyboardInterrupt) else "unverified",
                           ended=None, duration=None, reason=str(exc))
            try:
                records.lifecycle(attempt, "finished")
            except BaseException:
                pass  # Preserve the original failure; the prepared attempt remains incomplete.
            raise
        records.lifecycle(attempt, "finished")
        return attempt

    def execute(self, *, worker_factory=CodexWorker, validator_factory=IsolatedValidator,
                codex_path=None, steps=None):
        from .workflow_execution import execute
        return execute(self, worker_factory=worker_factory, validator_factory=validator_factory,
                       codex_path=codex_path, steps=steps)

    def resume(self, *, worker_factory=CodexWorker, validator_factory=IsolatedValidator,
               codex_path=None, steps=None):
        from .workflow_recovery import resume
        return resume(self, worker_factory=worker_factory, validator_factory=validator_factory,
                      codex_path=codex_path, steps=steps)

    def recovery_status(self):
        from .workflow_recovery import recovery_status
        return recovery_status(self)

    def report(self):
        from .results import report
        return report(self)

    def acceptance_status(self):
        from .workflow_acceptance import acceptance_status
        return acceptance_status(self)

    def record_reuse(self, requirement_id, validation_ids, evidence, **options):
        from .workflow_acceptance import record_reuse
        with ProjectLock(self.store):
            return record_reuse(self, requirement_id, validation_ids, evidence, **options)

    def record_manual(self, check_id, outcome, evidence, **options):
        from .workflow_acceptance import record_manual
        with ProjectLock(self.store):
            return record_manual(self, check_id, outcome, evidence, **options)

    def accept(self):
        from .workflow_acceptance import accept
        with ProjectLock(self.store):
            return accept(self)

    def feedback(self, text, *, kind, task_id=None, feedback_id=None):
        from .workflow_feedback import submit_feedback
        with ProjectLock(self.store):
            return submit_feedback(self, text, kind=kind, task_id=task_id, feedback_id=feedback_id)

    def cancel(self):
        with ProjectLock(self.store):
            run = self.get()
            if run["stage"] == "cancelled":
                return run
            if run["stage"] in {"accepted", "superseded"}:
                raise HarnessError("A completed or superseded workflow cannot be cancelled.")
            if any(alive(item.get("process")) for item in run["attempts"]):
                raise HarnessError("A recorded worker is still active; cannot cancel.")
            def cancel(current):
                current.update(stage="cancelled", reason="Explicitly cancelled; records and files preserved.")
                now = time.time()
                for wait in current["waits"]:
                    if wait["ended"] is None:
                        wait.update(ended=now, duration=now - wait["started"] if now >= wait["started"] else None)
            return self.store.transition(run["id"], run["id"] + ":cancelled", "workflow_cancelled", {}, cancel)

    def status(self):
        run = self.get()
        result = {key: copy.deepcopy(run[key]) for key in (
            "id", "kind", "phase_id", "planning_run_id", "plan_version", "plan_hash", "input_hash",
            "content_version", "policy_hash", "stage", "approval", "attempts", "findings", "waits", "reason")}
        result.update(WorkflowRecords(self.store, run["id"]).summary())
        result["initial_content_version"] = run.get("initial_content_version", run["content_version"])
        result["max_corrections"] = run["policy"]["max_corrections"]
        result["execution"] = copy.deepcopy(run.get("execution"))
        result["recoveries"] = copy.deepcopy(run.get("recoveries", []))
        result["recovery"] = self.recovery_status()
        result["acceptance"] = self.acceptance_status()
        result["feedback"] = copy.deepcopy(run.get("feedback", []))
        result["pending_record_attempts"] = self._pending(run)
        result["pending_review_attempts"] = [item["id"] for raw in run["attempts"] for item in [effective_attempt(raw)]
            if item["role"] == "reviewer" and item.get("outcome") == "validated" and not item.get("findings_ingested")]
        available = run["policy"].get("workflow_version") == 1
        result.update(database=str(self.store.path), execution_authorized=run["approval"] is not None and
                      run["stage"] in {"execution_ready", "executing", "technically_complete"},
                      workflow_execution_enabled=available, orchestration_available=available)
        try:
            self._check(run)
        except (HarnessError, OSError) as exc:
            result["inspection_error"] = str(exc)
        return result
