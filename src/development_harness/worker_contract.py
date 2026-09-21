"""Bounded role messages and controller-owned file changes for P3-T2.

These components do not approve a plan or admit a workflow. The caller supplies
the reviewed task scope; the version-bound admission coordinator is P3-T3.
"""

import copy
import hashlib
import json
import os
from pathlib import Path
import re

from .files import apply_write, require_snapshot, snapshot, target
from .model import HarnessError, digest, relative_path
from .plan_schema import TEXT, array, obj
from .project import MAX_CONTEXT_BYTES, MAX_FILE_BYTES, SECRET_PATTERN, SENSITIVE_PARTS, source
from .store import check_home


DEVELOPER_SCHEMA = obj(task_id=TEXT, status={"type": "string", "enum": ["changes", "unchanged", "blocked"]},
                       summary=TEXT, changes=array(obj(path=TEXT, base_sha256=TEXT, content=TEXT)), questions=array(TEXT))
REVIEWER_SCHEMA = obj(task_id=TEXT, verdict={"type": "string", "enum": ["pass", "changes", "blocked"]},
                      summary=TEXT, findings=array(obj(id=TEXT, requirement_id=TEXT, path=TEXT,
                          severity={"type": "string", "enum": ["critical", "high", "medium", "low"]},
                          required={"type": "boolean"}, evidence=TEXT, recommendation=TEXT)), questions=array(TEXT))


def save_record(path, value):
    path = Path(path)
    temporary = path.with_suffix(path.suffix + ".tmp")
    with temporary.open("w", encoding="utf-8", newline="\n") as stream:
        json.dump(value, stream, ensure_ascii=False, indent=2)
        stream.write("\n")
        stream.flush()
        os.fsync(stream.fileno())
    os.replace(temporary, path)


def _shape(value, schema):
    kind = schema["type"]
    if type(value) is not {"object": dict, "array": list, "string": str, "boolean": bool}[kind]:
        raise HarnessError("Worker response has an invalid field type.")
    if kind == "object":
        if set(value) != set(schema["properties"]):
            raise HarnessError("Worker response contains missing or unexpected fields.")
        for key, child in schema["properties"].items():
            _shape(value[key], child)
    elif kind == "array":
        if len(value) > 100:
            raise HarnessError("Worker response contains too many items.")
        for item in value:
            _shape(item, schema["items"])
    elif kind == "string":
        if len(value.encode("utf-8")) > MAX_FILE_BYTES or "\0" in value:
            raise HarnessError("Worker response text is oversized or binary.")
        if "enum" in schema and value not in schema["enum"]:
            raise HarnessError("Worker response contains an unknown outcome.")


def editable_path(name):
    relative_path(name)
    parts = [p.casefold() for p in name.split("/")]
    if (set(parts) & (SENSITIVE_PARTS | {"harness-project.json", ".harness-output"}) or
            parts[:2] == ["phase", "generated"] or any(p.startswith(".env") for p in parts) or
            parts[-1].endswith((".env", ".pem", ".key", ".pfx", ".p12"))):
        raise HarnessError("Worker cannot change configuration, generated plans, credentials or control paths: " + name)
    return name


class TaskScope:
    def __init__(self, project, task_id, requirements, editable_paths, context_paths, *, instructions=""):
        self.project = Path(project).resolve(strict=True)
        if not re.fullmatch(r"[A-Za-z0-9][A-Za-z0-9_-]{0,63}", task_id):
            raise HarnessError("A bounded task identifier is required.")
        if (not isinstance(requirements, dict) or not requirements or len(requirements) > 100 or
                any(not isinstance(k, str) or not isinstance(v, str) or not k.strip() or not v.strip()
                    for k, v in requirements.items())):
            raise HarnessError("Task requirements must map identifiers to explicit text.")
        self.task_id, self.requirements = task_id, copy.deepcopy(requirements)
        self.instructions = instructions
        self.editable = tuple(editable_path(name) for name in editable_paths)
        self.context_paths = tuple(context_paths)
        if not self.editable or len(self.editable) > 100 or len(set(p.casefold() for p in self.editable)) != len(self.editable):
            raise HarnessError("Editable file paths must be nonempty, bounded and case-unique.")
        names = list(dict.fromkeys([*context_paths, *self.editable]))
        if len(set(p.casefold() for p in names)) != len(names):
            raise HarnessError("Context paths must be case-unique.")
        self.baseline = snapshot(self.project)
        canonical = {name.casefold(): name for name in self.baseline}
        self.files = []
        for name in names:
            editable_path(name)  # The same sensitive/control exclusions apply to AI context.
            if name.casefold() in canonical and canonical[name.casefold()] != name:
                raise HarnessError("Use the exact existing file-name case: " + name)
            path = target(self.project, name)
            if name in self.editable:
                editable_path(name)
            if path.exists():
                self.files.append(source(self.project, name))
            elif name in self.editable:
                self.files.append({"path": name, "sha256": "absent", "text": ""})
            else:
                raise HarnessError("Selected context file is missing: " + name)
        self.check()
        raw = json.dumps(self.packet(), ensure_ascii=False).encode("utf-8")
        if len(raw) > MAX_CONTEXT_BYTES or SECRET_PATTERN.search(raw.decode("utf-8")):
            raise HarnessError("Worker context exceeds the budget or contains credential-like text.")

    def check(self):
        return require_snapshot(self.project, self.baseline)

    def packet(self):
        return copy.deepcopy({"task_id": self.task_id, "requirements": self.requirements,
                              "instructions": self.instructions, "editable_paths": list(self.editable),
                              "content_version": digest(self.baseline), "files": self.files})

    def refresh(self):
        return TaskScope(self.project, self.task_id, self.requirements, self.editable,
                         self.context_paths, instructions=self.instructions)


def validate_proposal(value, scope):
    _shape(value, DEVELOPER_SCHEMA)
    if len(json.dumps(value, ensure_ascii=False).encode("utf-8")) > MAX_CONTEXT_BYTES * 2:
        raise HarnessError("Developer response exceeds the bounded output size.")
    if value["task_id"] != scope.task_id or not value["summary"].strip():
        raise HarnessError("Developer response does not identify this task and its result.")
    changes = value["changes"]
    if len({item["path"].casefold() for item in changes}) != len(changes):
        raise HarnessError("Developer changes contain duplicate file paths.")
    if (value["status"] == "changes") != bool(changes):
        raise HarnessError("Developer status contradicts the proposed changes.")
    if value["status"] == "blocked" and not value["questions"]:
        raise HarnessError("A blocked Developer must explain the question preventing work.")
    total = 0
    for change in changes:
        name = editable_path(change["path"])
        if name not in scope.editable:
            raise HarnessError("Developer change is outside the reviewed file scope: " + name)
        if change["base_sha256"] != scope.baseline.get(name, "absent"):
            raise HarnessError("Developer change targets a different file version: " + name)
        if SECRET_PATTERN.search(change["content"]):
            raise HarnessError("Credential-like content cannot be applied as a worker change.")
        total += len(change["content"].encode("utf-8"))
    if total > MAX_CONTEXT_BYTES:
        raise HarnessError("Developer change set exceeds the bounded output size.")
    return value


def validate_review(value, scope):
    _shape(value, REVIEWER_SCHEMA)
    if len(json.dumps(value, ensure_ascii=False).encode("utf-8")) > MAX_CONTEXT_BYTES * 2:
        raise HarnessError("Reviewer response exceeds the bounded output size.")
    if value["task_id"] != scope.task_id or not value["summary"].strip():
        raise HarnessError("Reviewer response does not identify this task and its result.")
    ids = set()
    for finding in value["findings"]:
        if (not re.fullmatch(r"[A-Za-z0-9][A-Za-z0-9_-]{0,63}", finding["id"]) or finding["id"] in ids or
                finding["requirement_id"] not in scope.requirements):
            raise HarnessError("Reviewer finding has an invalid identity or requirement reference.")
        ids.add(finding["id"])
        if finding["path"] and finding["path"] not in {item["path"] for item in scope.files}:
            raise HarnessError("Reviewer finding refers to a file outside the supplied context.")
        if not finding["evidence"].strip() or not finding["recommendation"].strip():
            raise HarnessError("Reviewer findings require evidence and a concrete follow-up.")
        if finding["severity"] in {"critical", "high"} and not finding["required"]:
            raise HarnessError("High/critical review findings cannot be optional.")
    required = any(finding["required"] for finding in value["findings"])
    if value["verdict"] == "pass" and required or value["verdict"] == "changes" and not required:
        raise HarnessError("Reviewer verdict contradicts mandatory findings.")
    if value["verdict"] == "blocked" and not value["questions"]:
        raise HarnessError("A blocked Reviewer must identify its unanswered question.")
    return value


def apply_proposal(scope, proposal, directory):
    """Preflight the entire proposal, then compare/write each permitted file.

    A file race/I/O interruption may leave a recorded partial patch. Never roll
    back over user edits. P3-T5 will coordinate explicit recovery of that state.
    """
    validate_proposal(proposal, scope)
    scope.check()
    if proposal["status"] == "blocked":
        raise HarnessError("Blocked Developer output cannot be applied.")
    directory = check_home(directory, scope.project)
    directory.mkdir(parents=True, exist_ok=False)
    record = {"task_id": scope.task_id, "before": scope.baseline, "proposal": proposal,
              "applied": [], "outcome": "prepared"}
    save_record(directory / "patch.json", record)
    expected = dict(scope.baseline)
    try:
        for change in proposal["changes"]:
            require_snapshot(scope.project, expected)
            name = change["path"]
            apply_write(scope.project, name, change["content"], expected.get(name))
            expected[name] = hashlib.sha256(change["content"].encode("utf-8")).hexdigest()
            record["applied"].append({"path": name, "sha256": expected[name]})
            save_record(directory / "patch.json", record)
        require_snapshot(scope.project, expected)
        record.update(outcome="applied", after=expected, content_version=digest(expected))
    except BaseException as exc:
        record.update(outcome="partial", reason=str(exc), expected_after_partial=expected)
        raise
    finally:
        save_record(directory / "patch.json", record)
    return record
