"""Explicit project inputs, bounded context collection and immutable artifacts."""

import hashlib
import json
from pathlib import Path
import re

from .files import apply_write, require_single_link, snapshot, target
from .model import HarnessError, digest, validate_checks


CONFIG = "harness-project.json"
OUTPUT = "Phase/Generated"
MAX_FILE_BYTES = 128_000
MAX_CONTEXT_BYTES = 320_000
SENSITIVE_PARTS = {".git", ".codex", ".agents", ".ssh", ".aws", "node_modules", "credentials", "secrets"}
SECRET_PATTERN = re.compile(r"-----BEGIN (?:RSA |EC |OPENSSH )?PRIVATE KEY-----|\b(?:sk-proj-|sk-svcacct-|ghp_|github_pat_)[A-Za-z0-9_-]{16,}")


def decode_json(text):
    def pairs(items):
        result = {}
        for key, value in items:
            if key in result:
                raise ValueError("Duplicate JSON key: " + key)
            result[key] = value
        return result
    def constant(value):
        raise ValueError("Non-finite JSON value: " + value)
    try:
        return json.loads(text, object_pairs_hook=pairs, parse_constant=constant)
    except (TypeError, ValueError) as exc:
        raise HarnessError("Cannot read JSON input: " + str(exc)) from exc


def read_json(path):
    try:
        return decode_json(Path(path).read_text(encoding="utf-8-sig"))
    except OSError as exc:
        raise HarnessError("Cannot read JSON input: " + str(exc)) from exc


def source(root, name):
    path = target(root, name)
    parts = {p.lower() for p in Path(name).parts}
    leaf = path.name.lower()
    if parts & SENSITIVE_PARTS or leaf.startswith(".env") or leaf.endswith((".env", ".pem", ".key", ".pfx", ".p12")):
        raise HarnessError("Sensitive/non-source path cannot be sent to the Planner: " + name)
    if name == CONFIG or name.startswith(OUTPUT + "/"):
        raise HarnessError("Generated/configuration files are not specification/code inputs: " + name)
    try:
        before = path.stat()
        require_single_link(path, before)
        if before.st_size > MAX_FILE_BYTES:
            raise HarnessError("Planner input is too large; choose narrower source files: " + name)
        raw = path.read_bytes()
        target(root, name)
        after = path.stat()
        require_single_link(path, after)
        if (before.st_ino, before.st_mtime_ns, before.st_size) != (after.st_ino, after.st_mtime_ns, after.st_size):
            raise HarnessError("Planner input changed while reading: " + name)
        text = raw.decode("utf-8-sig")
    except (OSError, UnicodeError) as exc:
        raise HarnessError("Cannot read UTF-8 project input " + name + ": " + str(exc)) from exc
    if "\0" in text or SECRET_PATTERN.search(text):
        raise HarnessError("Binary or credential-like content excluded from Planner input: " + name)
    return {"path": name, "sha256": hashlib.sha256(raw).hexdigest(), "text": text}


def validate_config(root, config):
    expected = {"version", "spec", "context", "validation", "model", "planner_timeout"}
    if not isinstance(config, dict) or set(config) != expected or type(config["version"]) is not int or config["version"] != 1:
        raise HarnessError("Project configuration must contain version=1, spec, context, validation, model and planner_timeout.")
    if not isinstance(config["spec"], str) or Path(config["spec"]).suffix.lower() not in {".md", ".txt"}:
        raise HarnessError("Select a Markdown or UTF-8 text specification within the project.")
    context = config["context"]
    if not isinstance(context, list) or any(not isinstance(x, str) for x in context):
        raise HarnessError("context must list explicit relative project source files.")
    names = [config["spec"], *context]
    if len({x.casefold() for x in names}) != len(names):
        raise HarnessError("Specification/context paths must be unique, including letter case.")
    if not isinstance(config["model"], str) or not config["model"].strip() or len(config["model"]) > 100:
        raise HarnessError("A nonempty model name is required.")
    if type(config["planner_timeout"]) is not int or not 10 <= config["planner_timeout"] <= 1800:
        raise HarnessError("planner_timeout must be an integer between 10 and 1800 seconds.")
    validate_checks(config["validation"])
    files = [source(root, name) for name in names]
    if sum(len(x["text"].encode("utf-8")) for x in files) > MAX_CONTEXT_BYTES:
        raise HarnessError("Planner context exceeds the input budget; select fewer related files.")
    return files


def load_project(root):
    path = target(root, CONFIG)
    if path.exists():
        require_single_link(path, path.stat())
    config = read_json(path)
    return config, validate_config(root, config)


def content_baseline(root):
    # Generated plans are versioned separately; arbitrary user files stay in the baseline.
    return {name: value for name, value in snapshot(root).items() if not name.startswith(OUTPUT + "/")}


def require_baseline(root, baseline):
    if content_baseline(root) != baseline:
        raise HarnessError("Project inputs changed; preserve files and register a new planning run after inspection.")


def save_new(root, name, content):
    path = target(root, name)
    if path.exists():
        if path.read_bytes() != content.encode("utf-8"):
            raise HarnessError("Existing artifact differs; preserved: " + name)
        require_single_link(path, path.stat())
        return
    apply_write(root, name, content, None)


def packet_hash(files):
    return digest([{k: item[k] for k in ("path", "sha256")} for item in files])
