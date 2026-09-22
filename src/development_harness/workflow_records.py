"""Controller-owned, replay-safe evidence for real workflow execution.

This module records observations; it does not dispatch, retry, or recover work.
The admission coordinator is responsible for authorization before invocation.
"""

import copy
import math
import time
import uuid

from .model import HarnessError, digest
from .worker_contract import validate_review_assessments


ROLES = {"developer", "reviewer", "validation"}
PHASES = {"prepared", "process_registered", "dispatch_intent", "responded", "finished"}
DISPOSITIONS = {"open", "resolved", "false_positive", "deferred"}


def effective_attempt(record):
    """Read reconciled facts without rewriting the original lifecycle observations."""
    result = copy.deepcopy(record)
    recovery = record.get("recovery", {})
    result.update(copy.deepcopy(recovery.get("observations", {})))
    disposition = recovery.get("disposition")
    if disposition == "validated":
        result.update(outcome="validated", dispatch_status="responded",
                      actual_ai_call_attempts=1, confirmed_ai_calls=1)
        # Null explicitly means no original completion time was observed.
        result["journal_phases"].setdefault("finished", result.get("finished_at"))
    elif disposition == "not_sent":
        result.update(outcome="recovered_not_sent", dispatch_status="not_sent",
                      actual_ai_call_attempts=0, confirmed_ai_calls=0)
    elif disposition == "validation_interrupted":
        result.update(outcome="interrupted", failure_kind="interrupted", stop_kind="interrupted")
    return result


def reconciled_retry(record):
    return record.get("recovery", {}).get("disposition") in {"not_sent", "validation_interrupted"}


def validate_recovery_observations(current, observations):
    """Apply the same observational checks to read-only inspection and commit."""
    allowed = {"input_hash", "process", "containment", "started", "ended", "duration", "session_id", "response_hash",
               "usage", "cost", "review_verdict", "review_findings_hash", "review_validation_ids",
               "review_validation_hashes", "review_prior_findings", "review_prior_findings_hash",
               "review_assessments_hash", *(name + "_at" for name in PHASES)}
    if observations.keys() - allowed:
        raise HarnessError("Recovery cannot replace attempt identity or original lifecycle history.")
    for key, value in observations.items():
        if current.get(key) is not None and current[key] != value:
            raise HarnessError("Recovery cannot replace an existing observation: " + key)
    combined = {**current, **observations}
    for key in ("started", "ended", "duration", "cost", *(name + "_at" for name in PHASES)):
        _time(combined.get(key))
    if combined.get("duration") is not None:
        if (combined.get("started") is None or combined.get("ended") is None or
                combined["ended"] < combined["started"] or not math.isclose(
                    combined["duration"], combined["ended"] - combined["started"], rel_tol=1e-9, abs_tol=1e-9)):
            raise HarnessError("Recovered duration does not match observed start and end times.")


def _text(value, label):
    if not isinstance(value, str) or not value.strip():
        raise HarnessError(label + " must be nonempty text.")
    return value


def _time(value):
    if value is not None and (type(value) not in {int, float} or not math.isfinite(value) or value < 0):
        raise HarnessError("Observed times must be finite nonnegative numbers or null.")
    return value


def _attempt(run, attempt_id):
    for item in run["attempts"]:
        if item["id"] == attempt_id:
            return item
    raise HarnessError("Unknown workflow attempt: " + str(attempt_id))


def _task(run, task_id):
    for task in run["tasks"]:
        if task["id"] == task_id:
            return task
    raise HarnessError("Attempt refers to a task outside the approved plan.")


def _version(run):
    return digest(run["expected"])


class WorkflowRecords:
    def __init__(self, store, run_id):
        self.store, self.run_id = store, run_id
        self._check(store.get(run_id))

    @staticmethod
    def _check(run):
        if run.get("kind") != "workflow":
            raise HarnessError("Workflow evidence requires a workflow run.")

    def _transition(self, identity, kind, detail, update):
        def guarded(run):
            self._check(run)
            update(run)
        return self.store.transition(self.run_id, self.run_id + ":" + identity, kind, detail, guarded)

    def prepare_attempt(self, task_id, role, content_version, input_hash=None, attempt_id=None):
        """Commit the controller identity before the worker may be dispatched."""
        if role not in ROLES:
            raise HarnessError("Unknown workflow role.")
        _text(content_version, "Content version")
        if input_hash is not None:
            _text(input_hash, "Input hash")
        attempt_id = _text(attempt_id or uuid.uuid4().hex, "Attempt identity")
        detail = dict(id=attempt_id, task_id=task_id, role=role,
                      content_version=content_version, input_hash=input_hash)

        def update(run):
            _task(run, task_id)
            if content_version != _version(run):
                raise HarnessError("Attempt content version differs from the admitted code.")
            if any(item["id"] == attempt_id for item in run["attempts"]):
                raise HarnessError("Attempt identity already exists.")
            for previous in run["attempts"]:
                if previous["task_id"] == task_id and previous["role"] == role:
                    if reconciled_retry(previous):
                        continue
                    previous = effective_attempt(previous)
                    if ("finished" not in previous.get("journal_phases", {}) or
                            previous.get("dispatch_status") == "uncertain"):
                        raise HarnessError("An unfinished or uncertain attempt requires explicit reconciliation before another call.")
            run["attempts"].append({**detail, "plan_hash": run["plan_hash"],
                "policy_hash": run["policy_hash"], "outcome": "prepared", "dispatch_status": "not_sent",
                "actual_ai_call_attempts": 0, "confirmed_ai_calls": 0,
                "started": None, "ended": None, "duration": None, "usage": None, "cost": None,
                "journal_phases": {}})

        run = self._transition("attempt:" + attempt_id + ":create", "workflow_attempt_prepared", detail, update)
        return copy.deepcopy(_attempt(run, attempt_id))

    def recover_attempt(self, attempt_id, *, disposition, evidence, observations=None):
        """Append a separate, idempotent recovery decision; preserve the original attempt."""
        if disposition not in {"not_sent", "validated", "validation_interrupted"} or not isinstance(evidence, dict):
            raise HarnessError("Invalid attempt recovery disposition or evidence.")
        observations = copy.deepcopy(observations or {})
        detail = {"attempt_id": attempt_id, "disposition": disposition,
                  "evidence": copy.deepcopy(evidence), "observations": observations}

        def update(run):
            current = _attempt(run, attempt_id)
            if current.get("recovery"):
                raise HarnessError("Attempt already has a different recovery decision.")
            if disposition == "validation_interrupted":
                if current["role"] != "validation" or current.get("outcome") in {"passed", "failed"}:
                    raise HarnessError("Only an incomplete validation can be reconciled for retry.")
            elif current["role"] not in {"developer", "reviewer"}:
                raise HarnessError("AI recovery requires a Developer or Reviewer attempt.")
            if disposition == "not_sent" and ("dispatch_intent" in current.get("journal_phases", {}) or
                    current.get("responded_at") is not None or current.get("confirmed_ai_calls") == 1):
                raise HarnessError("A dispatched AI attempt cannot be classified as unsent.")
            if disposition == "validated" and (not observations.get("response_hash") or
                    not observations.get("session_id") or not observations.get("input_hash")):
                raise HarnessError("Validated recovery requires bound input, output and session evidence.")
            validate_recovery_observations(current, observations)
            current["recovery"] = {**detail, "at": time.time(), "original_hash": digest(current)}

        run = self._transition("attempt:" + attempt_id + ":recovery", "workflow_attempt_reconciled", detail, update)
        return effective_attempt(_attempt(run, attempt_id))

    def lifecycle(self, record, phase):
        """Worker callback: persist each observed phase once, with immutable identity."""
        if phase not in PHASES or not isinstance(record, dict):
            raise HarnessError("Invalid workflow lifecycle observation.")
        attempt_id = _text(record.get("id"), "Attempt identity")
        payload = copy.deepcopy({key: value for key, value in record.items()
                                 if key not in {"journal_phases", "finding_ids", "findings_ingested"}})
        for key in ("started", "ended", "duration", *(name + "_at" for name in PHASES)):
            _time(payload.get(key))
        _time(payload.get("cost"))
        if payload.get("duration") is not None and (payload.get("started") is None or payload.get("ended") is None):
            raise HarnessError("A duration requires observed start and end times.")
        if payload.get("started") is not None and payload.get("ended") is not None:
            if payload["ended"] < payload["started"]:
                raise HarnessError("Observed completion precedes attempt start.")
            if payload.get("duration") is not None and not math.isclose(
                    payload["duration"], payload["ended"] - payload["started"], rel_tol=1e-9, abs_tol=1e-9):
                raise HarnessError("Observed duration does not match the recorded start and end.")

        def update(run):
            current = _attempt(run, attempt_id)
            if current.get("recovery"):
                raise HarnessError("A reconciled attempt cannot accept new lifecycle observations.")
            for key in ("id", "task_id", "role", "content_version", "plan_hash", "policy_hash"):
                if payload.get(key) != current.get(key):
                    raise HarnessError("Attempt identity/version mismatch: " + key)
            if current.get("input_hash") is not None and payload.get("input_hash") != current["input_hash"]:
                raise HarnessError("Attempt input hash cannot change after binding.")
            if payload.get("input_hash") is not None:
                _text(payload["input_hash"], "Input hash")
            for key in ("process", "containment", "started", "ended", "duration", "session_id", "response_hash", "usage", "cost",
                        "review_prior_findings", "review_prior_findings_hash", "review_assessments_hash",
                        *(name + "_at" for name in PHASES)):
                if current.get(key) is not None and payload.get(key) != current[key]:
                    raise HarnessError("A recorded observation cannot change: " + key)
            prior = current["journal_phases"]
            if "finished" in prior:
                raise HarnessError("A finished attempt cannot accept new lifecycle observations.")
            required = {"process_registered": "prepared", "dispatch_intent": "process_registered", "responded": "dispatch_intent"}
            if phase in required and required[phase] not in prior:
                raise HarnessError("Lifecycle observation is out of order.")
            if phase == "responded":
                _text(payload.get("response_hash"), "Observed response hash")
            if phase == "finished" and current["role"] != "validation" and payload.get("outcome") == "validated" and "responded" not in prior:
                raise HarnessError("Validated AI output requires an observed response.")
            current.update(payload)
            prior[phase] = payload.get(phase + "_at")
            is_ai = current["role"] != "validation"
            dispatched = "dispatch_intent" in prior or current.get("dispatch_status") == "uncertain"
            # A responded event may fail to commit while the later final callback
            # succeeds. Preserve the independently observed response in that final
            # event without promoting its unverified outcome or inventing a phase.
            final_response = (phase == "finished" and "dispatch_intent" in prior and
                              payload.get("responded_at") is not None and payload.get("confirmed_ai_calls") == 1 and
                              payload.get("dispatch_status") == "responded" and
                              isinstance(payload.get("response_hash"), str) and bool(payload["response_hash"]))
            responded = "responded" in prior or final_response
            current["actual_ai_call_attempts"] = int(is_ai and dispatched)
            current["confirmed_ai_calls"] = (1 if responded else None if dispatched else 0) if is_ai else 0
            current["dispatch_status"] = "responded" if responded else "uncertain" if dispatched else "not_sent"
            if current.get("ended") is None:
                current["duration"] = None

        run = self._transition("attempt:" + attempt_id + ":" + phase, "workflow_attempt_" + phase, payload, update)
        return copy.deepcopy(_attempt(run, attempt_id))

    def start_wait(self, reason, wait_id=None, started=None):
        """Persist one wait interval. Replaying the ID never resets its clock."""
        _text(reason, "Wait reason")
        wait_id = _text(wait_id or uuid.uuid4().hex, "Wait identity")
        _time(started)
        detail = {"id": wait_id, "reason": reason, "started": started}

        def update(run):
            if any(item["id"] == wait_id for item in run["waits"]):
                raise HarnessError("Wait identity already exists.")
            run["waits"].append({**detail, "started": time.time() if started is None else started,
                                 "ended": None, "duration": None})

        run = self._transition("wait:" + wait_id + ":start", "workflow_wait_started", detail, update)
        return copy.deepcopy(next(item for item in run["waits"] if item["id"] == wait_id))

    def finish_wait(self, wait_id, ended=None):
        _text(wait_id, "Wait identity")
        _time(ended)

        def update(run):
            interval = next((item for item in run["waits"] if item["id"] == wait_id), None)
            if interval is None:
                raise HarnessError("Unknown wait interval.")
            if interval["ended"] is not None:
                raise HarnessError("Wait interval already ended.")
            finish = time.time() if ended is None else ended
            if interval["started"] is not None and finish < interval["started"]:
                raise HarnessError("Wait completion precedes its start.")
            interval.update(ended=finish, duration=None if interval["started"] is None else finish - interval["started"])

        run = self._transition("wait:" + wait_id + ":finish", "workflow_wait_finished", {"id": wait_id, "ended": ended}, update)
        return copy.deepcopy(next(item for item in run["waits"] if item["id"] == wait_id))

    def ingest_findings(self, attempt_id, findings, *, mapping=None):
        """Bind reviewer-local IDs to controller IDs; explicit mappings survive wording changes.

        Exact repeated findings are recognized automatically. Ambiguous similarity
        is never guessed. A controller can map a changed finding to a prior ID.
        """
        if not isinstance(findings, list) or not all(isinstance(item, dict) for item in findings):
            raise HarnessError("Findings must be a list of objects.")
        findings, mapping = copy.deepcopy(findings), copy.deepcopy(mapping or {})
        if not isinstance(mapping, dict):
            raise HarnessError("Finding identity mapping must be an object.")

        def update(run):
            self._ingest_findings(run, attempt_id, findings, mapping)

        run = self._transition("findings:" + attempt_id, "workflow_findings_observed",
                               {"attempt_id": attempt_id, "findings": findings, "mapping": mapping}, update)
        return [copy.deepcopy(run["findings"][key]) for key in _attempt(run, attempt_id)["finding_ids"]]

    def _ingest_findings(self, run, attempt_id, findings, mapping):
        reviewer = effective_attempt(_attempt(run, attempt_id))
        if (reviewer["role"] != "reviewer" or reviewer.get("outcome") != "validated" or
                "finished" not in reviewer["journal_phases"] or reviewer.get("review_findings_hash") != digest(findings)):
            raise HarnessError("Findings require the exact validated Reviewer response.")
        task = _task(run, reviewer["task_id"])
        local_ids, controller_ids = set(), []
        for item in findings:
            if set(item) != {"id", "requirement_id", "path", "severity", "required", "evidence", "recommendation"}:
                raise HarnessError("Finding contains missing or unexpected fields.")
            local_id = _text(item["id"], "Reviewer-local finding identity")
            if local_id in local_ids or item["requirement_id"] not in task["requirements"]:
                raise HarnessError("Finding identity or requirement reference is invalid.")
            local_ids.add(local_id)
            if (item["severity"] not in {"critical", "high", "medium", "low"} or
                    type(item["required"]) is not bool or
                    (item["severity"] in {"critical", "high"} and not item["required"])):
                raise HarnessError("Finding severity and mandatory status are invalid.")
            config = run.get("config", {})
            allowed_paths = set(task["paths"]) | set(config.get("context", []))
            allowed_paths.update(context["path"] for context in run.get("plan", {}).get("code_context", []))
            if config.get("spec"):
                allowed_paths.add(config["spec"])
            if not isinstance(item["path"], str) or item["path"] and item["path"] not in allowed_paths:
                raise HarnessError("Finding path is outside the approved task.")
            _text(item["evidence"], "Finding evidence")
            _text(item["recommendation"], "Finding recommendation")
            fingerprint = digest({key: value for key, value in item.items() if key != "id"})
            known = run["findings"]
            selected = mapping.get(local_id)
            if selected is not None:
                if selected not in known:
                    raise HarnessError("Finding mapping refers to an unknown controller identity.")
                previous = known[selected]
                if (previous["task_id"], previous["requirement_id"], previous["path"]) != (task["id"], item["requirement_id"], item["path"]):
                    raise HarnessError("Finding mapping crosses task, requirement or file scope.")
            else:
                matches = [key for key, value in known.items() if value["task_id"] == task["id"] and value["fingerprint"] == fingerprint]
                if len(matches) > 1:
                    raise HarnessError("Ambiguous repeated finding requires an explicit mapping.")
                selected = matches[0] if matches else "finding-" + digest([self.run_id, attempt_id, local_id])[:24]
            if selected in controller_ids:
                raise HarnessError("Two reviewer findings cannot map to the same controller identity.")
            if selected not in known:
                known[selected] = {"id": selected, "task_id": task["id"], "status": "open", "history": []}
            current = known[selected]
            mandatory = current.get("required", False) or item["required"]
            current.update({key: value for key, value in item.items() if key != "id"})
            current.update(required=mandatory, fingerprint=fingerprint, plan_hash=run["plan_hash"],
                           policy_hash=run["policy_hash"], content_version=reviewer["content_version"])
            if current["status"] in {"resolved", "false_positive"}:
                current["status"] = "open"
            current["history"].append({"kind": "observed", "attempt_id": attempt_id, "local_id": local_id,
                "content_version": reviewer["content_version"], "finding": copy.deepcopy(item), "status": current["status"]})
            controller_ids.append(selected)
        if not set(mapping) <= local_ids:
            raise HarnessError("Finding mapping contains an unobserved local identity.")
        _attempt(run, attempt_id).update(finding_ids=controller_ids, findings_ingested=True)

    def set_finding_status(self, finding_id, status, *, evidence, event_id=None):
        """Classify a finding with version-matched controller evidence, never self-report."""
        if status not in DISPOSITIONS or not isinstance(evidence, dict):
            raise HarnessError("Finding disposition requires structured evidence.")
        evidence = copy.deepcopy(evidence)
        _text(evidence.get("reason"), "Disposition reason")
        detail = {"finding_id": finding_id, "status": status, "evidence": evidence}
        event_id = event_id or digest(detail)

        def update(run):
            self._set_finding_status(run, finding_id, status, evidence)

        run = self._transition("finding-status:" + event_id, "workflow_finding_classified", detail, update)
        return copy.deepcopy(run["findings"][finding_id])

    def _set_finding_status(self, run, finding_id, status, evidence):
        if finding_id not in run["findings"]:
            raise HarnessError("Unknown controller finding identity.")
        finding = run["findings"][finding_id]
        if status in {"resolved", "false_positive"}:
            reviewer = effective_attempt(_attempt(run, evidence.get("reviewer_attempt_id")))
            if (reviewer["role"] != "reviewer" or reviewer.get("outcome") != "validated" or
                    reviewer.get("review_verdict") not in {"pass", "changes"} or
                    reviewer["task_id"] != finding["task_id"] or reviewer["content_version"] != _version(run) or
                    not reviewer.get("findings_ingested") or finding_id in reviewer["finding_ids"]):
                raise HarnessError("Closure requires a matching follow-up Reviewer with no repeated finding.")
            observations = [entry["attempt_id"] for entry in finding["history"] if entry["kind"] == "observed"]
            order = {item["id"]: index for index, item in enumerate(run["attempts"])}
            if order[reviewer["id"]] <= max(order[reference] for reference in observations):
                raise HarnessError("Closure requires a follow-up review after the latest finding observation.")
            if status == "resolved":
                references = evidence.get("validation_attempt_ids")
                if not isinstance(references, list) or not references or len(set(references)) != len(references):
                    raise HarnessError("Resolution requires distinct passing validation evidence.")
                if not set(references) <= set(reviewer.get("review_validation_ids", [])):
                    raise HarnessError("Resolution validation was not supplied to the follow-up Reviewer.")
                checks = set()
                for reference in references:
                    validation = effective_attempt(_attempt(run, reference))
                    if (validation["role"] != "validation" or validation.get("outcome") != "passed" or
                            "finished" not in validation["journal_phases"] or validation["task_id"] != finding["task_id"] or
                            validation["content_version"] != reviewer["content_version"] or not validation.get("check_hash") or
                            not max(order[reference] for reference in observations) < order[validation["id"]] < order[reviewer["id"]]):
                        raise HarnessError("Resolution validation is failed, incomplete or belongs to different code.")
                    checks.add(validation["check_hash"])
                required = {digest(check) for check in run["policy"]["validation"]}
                if not required <= checks:
                    raise HarnessError("Resolution is missing required validation checks.")
        finding["status"] = status
        finding["history"].append({"kind": "disposition", "status": status, "evidence": evidence,
                                    "content_version": _version(run)})

    def apply_review_assessments(self, attempt_id, response):
        """Atomically ingest findings and apply the exact independent follow-up verdict.

        A passing response alone does not close anything. The supplied prior
        controller snapshot and every explicit assessment remain bound to the
        worker input/output hashes and matching validation journal entries.
        """
        response = copy.deepcopy(response)

        def update(run):
            reviewer = effective_attempt(_attempt(run, attempt_id))
            previous = reviewer.get("review_prior_findings")
            if (reviewer["role"] != "reviewer" or reviewer.get("outcome") != "validated" or
                    "finished" not in reviewer["journal_phases"] or reviewer["content_version"] != _version(run) or
                    not isinstance(previous, list) or not previous or
                    reviewer.get("review_prior_findings_hash") != digest(previous) or
                    not isinstance(response, dict) or reviewer.get("response_hash") != digest(response) or
                    response.get("task_id") != reviewer["task_id"] or
                    reviewer.get("review_verdict") != response.get("verdict") or
                    reviewer.get("review_assessments_hash") != digest(response.get("assessments"))):
                raise HarnessError("Assessments require the exact validated follow-up response and current code.")
            validate_review_assessments(response, previous)
            prior_ids = {item["id"] for item in previous}
            unresolved = {key for key, item in run["findings"].items()
                          if item["task_id"] == reviewer["task_id"] and item["status"] in {"open", "deferred"}}
            if prior_ids != unresolved or len(prior_ids) != len(previous):
                raise HarnessError("Follow-up input must contain every unresolved task finding exactly once.")
            order = {item["id"]: index for index, item in enumerate(run["attempts"])}
            for item in previous:
                recorded = run["findings"][item["id"]]
                if (not {"id", "task_id", "requirement_id", "path", "required", "status"} <= set(item) or
                        any(recorded.get(key) != value for key, value in item.items())):
                    raise HarnessError("Follow-up prior findings differ from the controller record.")
                observations = [entry["attempt_id"] for entry in recorded["history"] if entry["kind"] == "observed"]
                if order[attempt_id] <= max(order[reference] for reference in observations):
                    raise HarnessError("Assessments require a follow-up review after the latest finding observation.")
            mapping = {item["id"]: item["id"] for item in response["findings"] if item["id"] in prior_ids}
            self._ingest_findings(run, attempt_id, response["findings"], mapping)
            for assessment in response["assessments"]:
                evidence = {"reason": assessment["reason"], "reviewer_evidence": assessment["evidence"],
                            "reviewer_attempt_id": attempt_id,
                            "assessment_hash": digest(assessment)}
                if assessment["status"] == "resolved":
                    evidence["validation_attempt_ids"] = reviewer.get("review_validation_ids", [])
                self._set_finding_status(run, assessment["finding_id"], assessment["status"], evidence)
            _attempt(run, attempt_id)["assessments_applied"] = True

        run = self._transition("review-assessments:" + attempt_id, "workflow_review_assessed",
                               {"attempt_id": attempt_id, "response": response}, update)
        return [copy.deepcopy(item) for item in run["findings"].values()
                if item["task_id"] == _attempt(run, attempt_id)["task_id"]]

    def summary(self):
        run = self.store.get(self.run_id)
        attempts = [effective_attempt(item) for item in run["attempts"]]
        ai = [item for item in attempts if item["role"] in {"developer", "reviewer"}]
        uncertain = sum(item.get("dispatch_status") == "uncertain" for item in ai)
        durations = [item.get("duration") for item in attempts]
        waits = [item.get("duration") for item in run["waits"]]
        observed = [item for item in ai if item.get("confirmed_ai_calls") == 1]
        usage_keys = set().union(*(item["usage"].keys() for item in observed if isinstance(item.get("usage"), dict)))
        usage = {}
        for key in sorted(usage_keys):
            values = [item["usage"].get(key) if isinstance(item.get("usage"), dict) else None for item in observed]
            usage[key] = sum(values) if not uncertain and all(type(value) is int and value >= 0 for value in values) else None
        costs = [item.get("cost") for item in observed]
        cost = sum(costs) if costs and not uncertain and all(value is not None for value in costs) else None
        return {"attempt_count": len(attempts), "ai_dispatch_attempts": sum(item.get("actual_ai_call_attempts", 0) for item in ai),
                "confirmed_ai_calls": len(observed), "uncertain_ai_calls": uncertain,
                "total_ai_calls": None if uncertain else len(observed),
                "duration": None if any(value is None for value in durations) else sum(durations),
                "observed_duration": sum(value for value in durations if value is not None),
                "approval_wait": None if any(value is None for value in waits) else sum(waits),
                "observed_approval_wait": sum(value for value in waits if value is not None),
                "usage": usage or None, "cost": cost,
                "finding_count": len(run["findings"]),
                "blocking_findings": [key for key, value in run["findings"].items()
                                      if value["required"] and value["status"] in {"open", "deferred"}]}
