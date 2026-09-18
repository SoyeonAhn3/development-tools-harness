"""A text-only Codex Planner. Project tools are disabled, not prompt-restricted."""

import hashlib
import json
import os
from pathlib import Path
import shutil
import subprocess
import time
import tomllib

from .model import HarnessError
from .processes import Job, identity
from .project import decode_json


SUPPORTED_VERSION = "codex-cli 0.154.0"


def executable():
    candidates = [shutil.which("codex.exe"),
                  str(Path(os.environ.get("APPDATA", "")) / "npm/node_modules/@openai/codex/node_modules/"
                      "@openai/codex-win32-x64/vendor/x86_64-pc-windows-msvc/bin/codex.exe")]
    for name in candidates:
        if name and Path(name).is_file():
            return Path(name).resolve()
    raise HarnessError("Codex CLI executable not found. Install/login to the supported CLI first.")


def environment():
    # Do not inherit alternate providers, API keys, shell startup or repository Python hooks.
    allowed = {"systemroot", "windir", "comspec", "path", "pathext", "temp", "tmp", "userprofile",
               "homedrive", "homepath", "localappdata", "appdata", "programdata", "programfiles",
               "programfiles(x86)", "os", "processor_architecture", "number_of_processors",
               "codex_home", "codex_ca_certificate", "ssl_cert_file", "https_proxy", "http_proxy",
               "no_proxy"}
    return {k: v for k, v in os.environ.items() if k.lower() in allowed}


def default_model():
    home = Path(os.environ.get("CODEX_HOME", Path.home() / ".codex"))
    try:
        value = tomllib.loads((home / "config.toml").read_text(encoding="utf-8")).get("model")
    except (OSError, ValueError):
        value = None
    if not isinstance(value, str) or not value.strip():
        raise HarnessError("Specify --model, or configure a model in the Codex user configuration.")
    return value


def command_result(argv, cwd, timeout=20):
    try:
        return subprocess.run(argv, cwd=cwd, env=environment(), capture_output=True, text=True,
                              encoding="utf-8", errors="replace", timeout=timeout,
                              creationflags=subprocess.CREATE_NO_WINDOW)
    except (OSError, subprocess.TimeoutExpired) as exc:
        raise HarnessError("Cannot inspect the Codex CLI: " + str(exc)) from exc


class CodexPlanner:
    def __init__(self, model, directory):
        if not isinstance(model, str) or not model.strip() or len(model) > 100:
            raise HarnessError("A nonempty Codex model name is required.")
        self.model = model
        self.directory = Path(directory)
        self.directory.mkdir(parents=True, exist_ok=True)
        self.exe = executable()
        self.features = {}
        self.policy = None

    def inspect(self):
        version = command_result([str(self.exe), "--version"], self.directory)
        if version.returncode or version.stdout.strip() != SUPPORTED_VERSION:
            raise HarnessError("Unverified Codex CLI version; rerun/review permission compatibility before use.")
        auth = command_result([str(self.exe), "login", "status"], self.directory)
        if auth.returncode or "Logged in using ChatGPT" not in auth.stdout + auth.stderr:
            raise HarnessError("ChatGPT login required. Run codex login in your terminal, then retry.")
        result = command_result([str(self.exe), "features", "list"], self.directory)
        if result.returncode:
            raise HarnessError("Cannot inspect Codex feature controls.")
        self.features = {line.split()[0]: False for line in result.stdout.splitlines()
                         if line.strip() and "removed" not in line and "deprecated" not in line}
        required = {"shell_tool", "apps", "plugins", "hooks", "browser_use", "computer_use",
                    "code_mode_host", "view_image", "skip_host_skill_discovery"}
        if not required <= self.features.keys():
            raise HarnessError("Codex does not expose the required Planner capability controls.")
        self.features["skip_host_skill_discovery"] = True
        return {"version": SUPPORTED_VERSION, "executable": str(self.exe),
                "binary_hash": hashlib.sha256(self.exe.read_bytes()).hexdigest(), "model": self.model,
                "authentication": "chatgpt", "features": self.features}

    def arguments(self, schema=None, *, probe_url=None):
        args = [str(self.exe), "exec", "--ignore-user-config", "--ignore-rules", "--ephemeral",
                "--skip-git-repo-check", "--strict-config", "--json", "--color", "never",
                "-C", str(self.directory), "-s", "read-only", "-m", self.model]
        config = {"approval_policy": "never", "project_doc_max_bytes": 0, "web_search": "disabled",
                  "agents.enabled": False, "model_provider": "openai", "model_reasoning_effort": "medium",
                  "suppress_unstable_features_warning": True, "analytics.enabled": False,
                  "feedback.enabled": False, "forced_login_method": "chatgpt"}
        config.update({"features." + k: v for k, v in self.features.items()})
        if probe_url:
            config.update({"model_provider": "harness_probe", "model_providers.harness_probe.name": "Local capability probe",
                           "model_providers.harness_probe.base_url": probe_url,
                           "model_providers.harness_probe.wire_api": "responses",
                           "model_providers.harness_probe.requires_openai_auth": False})
        for key, value in config.items():
            args.extend(["-c", key + "=" + json.dumps(value)])
        if schema:
            args.extend(["--output-schema", str(schema)])
        return args + ["-"]

    def verify(self):
        from .codex_probe import verify_capabilities
        details = self.inspect()
        self.policy = {**details, **verify_capabilities(self), "verified_at": time.time(),
                       "boundary": "text-only; no filesystem, process, app or web tools"}
        return self.policy

    def generate(self, prompt, schema, attempt, launched, timeout=180):
        if self.policy is None:
            raise HarnessError("Verify the Planner capability boundary before a live call.")
        if hashlib.sha256(self.exe.read_bytes()).hexdigest() != self.policy["binary_hash"]:
            raise HarnessError("Codex executable changed after verification.")
        schema_path = self.directory / (attempt["id"] + ".schema.json")
        schema_path.write_text(json.dumps(schema), encoding="utf-8")
        log = self.directory / (attempt["id"] + ".jsonl")
        errors = self.directory / (attempt["id"] + ".stderr.log")
        attempt.update(model=self.model, policy=self.policy, log=str(log), stderr=str(errors),
                       outcome="launching", started=time.time())
        worker = None
        job = Job()
        try:
            with log.open("wb") as output, errors.open("wb") as error:
                worker = subprocess.Popen(self.arguments(schema_path), cwd=self.directory, env=environment(),
                                          stdin=subprocess.PIPE, stdout=output, stderr=error,
                                          creationflags=subprocess.CREATE_NO_WINDOW)
                job.assign(worker.pid)
                attempt.update(process=identity(worker.pid), outcome="running")
                launched(attempt)
                try:
                    worker.communicate(prompt.encode("utf-8"), timeout=timeout)
                except subprocess.TimeoutExpired:
                    attempt.update(outcome="interrupted", reason="Planner timeout; resume explicitly to retry.")
                    return None
                attempt["exit_code"] = worker.returncode
                if worker.returncode:
                    attempt.update(outcome="unverified", reason="Codex call failed; inspect the recorded logs and login/limits.")
                    return None
        except KeyboardInterrupt:
            attempt.update(outcome="interrupted", reason="Planner interrupted; resume explicitly to retry.")
            raise
        finally:
            job.close()
            if worker:
                if worker.stdin and not worker.stdin.closed:
                    worker.stdin.close()
                if worker.poll() is None:
                    worker.kill()
                worker.wait(timeout=10)
            if attempt["outcome"] == "interrupted":
                attempt.update(ended=None, duration=None)
            else:
                attempt["ended"] = time.time()
                attempt["duration"] = attempt["ended"] - attempt["started"]
        response, usage = parse_events(log.read_text(encoding="utf-8"))
        attempt["usage"] = usage
        attempt["outcome"] = "responded"
        return response


def parse_events(raw):
    messages, completed, usage = [], False, None
    for line in raw.splitlines():
        try:
            event = decode_json(line)
        except HarnessError as exc:
            raise HarnessError("Malformed Codex event stream; response not verified.") from exc
        if not isinstance(event, dict) or not isinstance(event.get("type"), str):
            raise HarnessError("Malformed Codex event; response not verified.")
        if event.get("type") in {"error", "turn.failed"}:
            raise HarnessError("Codex reported an unsuccessful turn; inspect the recorded event log.")
        if event.get("type") == "turn.completed":
            completed, usage = True, event.get("usage")
        item = event.get("item", {})
        if not isinstance(item, dict):
            raise HarnessError("Malformed Codex item; response not verified.")
        if item.get("type") == "error":
            raise HarnessError("Codex reported an item error; response not verified.")
        if item.get("type") not in {None, "agent_message", "reasoning", "error"}:
            raise HarnessError("Unexpected Planner tool event; permission evidence is invalid.")
        if event.get("type") == "item.completed" and item.get("type") == "agent_message":
            messages.append(item.get("text", ""))
    if not completed or not messages:
        raise HarnessError("Planner ended without a confirmed final response.")
    try:
        return decode_json(messages[-1]), usage
    except HarnessError as exc:
        raise HarnessError("Planner final response is not JSON; inspect the log and retry.") from exc
