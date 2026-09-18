"""Validate the small, explicit input contract used by the Phase 1 fake Adapter."""

import hashlib
import json
import math
from pathlib import Path, PurePosixPath


class HarnessError(Exception):
    """An actionable failure that must not be reported as successful work."""


def digest(value):
    return hashlib.sha256(json.dumps(value, sort_keys=True, ensure_ascii=True).encode()).hexdigest()


def file_digest(path):
    return hashlib.sha256(Path(path).read_bytes()).hexdigest()


EXCLUDED = {".git", ".venv", "__pycache__", ".pytest_cache", ".harness-output"}


def relative_path(value):
    if not isinstance(value, str) or not value or "\\" in value or ":" in value:
        raise HarnessError(f"Use a relative forward-slash file path: {value!r}")
    path = PurePosixPath(value)
    if path.is_absolute() or any(p.lower() in {"..", "."} | EXCLUDED for p in path.parts):
        raise HarnessError(f"Write path is outside the editable scope: {value}")
    reserved = {"con", "prn", "aux", "nul"} | {f"{prefix}{i}" for prefix in ("com", "lpt") for i in range(1, 10)}
    if any(p.split(".")[0].lower() in reserved or any(c in p for c in '<>"|?*\0') for p in path.parts):
        raise HarnessError(f"Unsupported Windows file name: {value}")
    if path.as_posix() != value or any(p.endswith((" ", ".")) for p in path.parts):
        raise HarnessError(f"Non-canonical write path: {value}")
    return value


def load_plan(path):
    try:
        raw = Path(path).read_bytes()
        plan = json.loads(raw)
    except (OSError, ValueError) as exc:
        raise HarnessError(f"Cannot read JSON plan: {exc}") from exc
    if not isinstance(plan, dict) or set(plan) - {"phase", "tasks", "validation", "max_corrections"}:
        raise HarnessError("Plan must contain phase, tasks, validation and optional max_corrections.")
    if not isinstance(plan.get("phase"), str) or not plan["phase"].strip():
        raise HarnessError("A nonempty phase identifier is required.")
    limit = plan.setdefault("max_corrections", 2)
    if type(limit) is not int or not 0 <= limit <= 10:
        raise HarnessError("max_corrections must be an integer between 0 and 10.")
    tasks = plan.get("tasks")
    if not isinstance(tasks, list) or not tasks:
        raise HarnessError("At least one task is required.")
    ids = set()
    for task in tasks:
        if not isinstance(task, dict) or set(task) - {"id", "writes", "review"}:
            raise HarnessError("A fake task contains id, writes and optional review only.")
        task_id = task.get("id")
        if not isinstance(task_id, str) or not task_id.strip() or task_id in ids:
            raise HarnessError("Task identifiers must be nonempty and unique.")
        ids.add(task_id)
        writes = task.get("writes")
        if not isinstance(writes, list) or not writes:
            raise HarnessError("writes must be a nonempty list of per-attempt file/text objects.")
        for batch in writes:
            if not isinstance(batch, dict):
                raise HarnessError("Each write attempt must be a file/text object.")
            for name, content in batch.items():
                relative_path(name)
                if not isinstance(content, str):
                    raise HarnessError("Fake file contents must be text.")
            if len({name.casefold() for name in batch}) != len(batch):
                raise HarnessError("Write paths cannot differ only in letter case.")
        review = task.setdefault("review", ["pass"])
        if not isinstance(review, list) or not review or any(not isinstance(x, str) or x not in {"pass", "changes"} for x in review):
            raise HarnessError("review must be a list containing pass or changes.")
    checks = plan.get("validation")
    validate_checks(checks)
    return plan, hashlib.sha256(raw).hexdigest()


def validate_checks(checks):
    """Shared command contract for fake execution and real project admission."""
    if not isinstance(checks, list) or not checks:
        raise HarnessError("At least one registered validation command is required.")
    has_tests = False
    for check in checks:
        if not isinstance(check, dict) or set(check) - {"argv", "kind", "timeout"}:
            raise HarnessError("Validation entries contain argv, kind and optional timeout.")
        argv = check.get("argv")
        if not isinstance(argv, list) or not argv or any(not isinstance(x, str) or not x for x in argv):
            raise HarnessError("argv must be a nonempty list of nonempty strings; no shell command strings.")
        if not isinstance(check.get("kind"), str) or check["kind"] not in {"pytest", "command"}:
            raise HarnessError("Validation kind must be pytest or command.")
        if check["kind"] == "pytest":
            has_tests = True
            if not (argv[:3] == ["{python}", "-m", "pytest"] or
                    len(argv) >= 3 and argv[1:3] == ["-m", "pytest"]):
                raise HarnessError("pytest commands must use a Python executable followed by -m pytest.")
            if any(x.startswith(("--junit", "--override-ini", "-o")) for x in argv[3:]):
                raise HarnessError("Harness-managed pytest evidence options cannot be overridden.")
        timeout = check.setdefault("timeout", 120)
        if type(timeout) not in {int, float} or not math.isfinite(timeout) or not 0 < timeout <= 3600:
            raise HarnessError("Validation timeout must be between 0 and 3600 seconds.")
    if not has_tests:
        raise HarnessError("At least one actual pytest check is required.")
    return checks
