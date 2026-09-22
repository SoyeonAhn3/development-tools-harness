"""A text-only Codex Planner. Project tools are disabled, not prompt-restricted."""

import hashlib
import json
import os
from pathlib import Path
import re
import shutil
import subprocess
import sys
import time
import tomllib

from .model import HarnessError, digest
from .processes import Job, identity
from .project import decode_json


# Versions share a profile only after its CLI contract and permission boundary are reviewed.
SUPPORTED_VERSIONS = {
    "codex-cli 0.154.0": "text-only-v1",
    "codex-cli 0.155.1": "text-only-v1",
}
REQUIRED_OPTIONS = {"--ignore-user-config", "--ignore-rules", "--ephemeral",
                    "--skip-git-repo-check", "--strict-config", "--json", "--color",
                    "--cd", "--sandbox", "--model", "--config", "--output-schema"}
REQUIRED_FEATURES = {"shell_tool", "apps", "plugins", "hooks", "browser_use", "computer_use",
                     "code_mode_host", "view_image", "skip_host_skill_discovery"}
CODEX_PATH_ENV = "DEVELOPMENT_HARNESS_CODEX_PATH"
DISABLED_CODE_MODE_NOTICE = ("Code Mode is unavailable because code-mode host is disabled. "
                            "Code mode will fail closed; enable `features.code_mode_host` "
                            "and install `codex-code-mode-host`.")

# This trusted bootstrap is inert until the controller has assigned its job and
# durably registered dispatch intent. If the controller dies before containment,
# its pipe closes and the gate exits without starting the target executable.
# -I prevents imports from the worker directory or inherited Python settings.
LAUNCH_GATE = """
import json, subprocess, sys
raw = sys.stdin.buffer.read()
if not raw:
    raise SystemExit(125)
request = json.loads(raw)
result = subprocess.run(request['argv'], input=request['prompt'].encode('utf-8'),
                        creationflags=subprocess.CREATE_NO_WINDOW, check=False)
raise SystemExit(result.returncode)
"""


def executable(selected=None):
    selected = selected if selected is not None else os.environ.get(CODEX_PATH_ENV)
    if selected is not None:
        path = Path(selected)
        if not path.is_absolute() or path.suffix.lower() != ".exe" or not path.is_file():
            raise HarnessError("Codex path must be an existing absolute .exe file: " + str(path))
        return path.resolve()
    candidates = [shutil.which("codex.exe"),
                  str(Path(os.environ.get("APPDATA", "")) / "npm/node_modules/@openai/codex/node_modules/"
                      "@openai/codex-win32-x64/vendor/x86_64-pc-windows-msvc/bin/codex.exe")]
    for name in candidates:
        if name and Path(name).is_file():
            return Path(name).resolve()
    raise HarnessError("Codex CLI executable not found. Select a reviewed CLI with --codex-path or " + CODEX_PATH_ENV + ".")


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
    def __init__(self, model, directory, *, codex_path=None):
        self.model = model
        self.directory = Path(directory)
        self.directory.mkdir(parents=True, exist_ok=True)
        # Explicit selection takes precedence over the user's machine-local environment setting.
        self.codex_path = codex_path if codex_path is not None else os.environ.get(CODEX_PATH_ENV)
        self.exe = None
        self.features = {}
        self.policy = None
        # Optional controller hook. Keep generate's existing call signature compatible
        # with planning adapters; workers also persist prepared/finished around it.
        self.lifecycle = None

    def inspect(self):
        self.policy = None
        self.features = {}
        report = {"ready": False, "version": None,
                  "executable": str(self.codex_path) if self.codex_path is not None else None,
                  "support_status": "unknown", "supported_versions": list(SUPPORTED_VERSIONS),
                  "profile": None, "model": self.model, "next_steps": [],
                  "checks": {name: {"status": "not_run"} for name in
                             ("executable", "version", "options", "features", "authentication", "model", "probe")}}

        def check(name, operation, action):
            try:
                operation()
            except (HarnessError, OSError) as exc:
                report["checks"][name] = {"status": "failed", "detail": str(exc)}
                report["next_steps"].append(action)
                return False
            report["checks"][name] = {"status": "passed"}
            return True

        def select():
            self.exe = executable(self.codex_path)
            report.update(executable=str(self.exe), binary_hash=hashlib.sha256(self.exe.read_bytes()).hexdigest())

        if not check("executable", select, "Specify an existing absolute .exe with --codex-path or " + CODEX_PATH_ENV + "."):
            return report

        def version():
            result = command_result([str(self.exe), "--version"], self.directory)
            observed = result.stdout.strip()
            if result.returncode or not re.fullmatch(r"codex-cli \d+\.\d+\.\d+(?:[-+][\w.-]+)?", observed):
                raise HarnessError("Cannot identify the selected Codex CLI version.")
            report["version"] = observed
            report["profile"] = SUPPORTED_VERSIONS.get(observed)
            report["support_status"] = "supported" if report["profile"] else "unverified"

        if not check("version", version, "Check the selected executable; it must report a Codex CLI version."):
            return report
        if report["support_status"] == "unverified":
            report["checks"]["version"] = {"status": "unverified", "detail": "This version has not been reviewed; incompatibility is not established."}
            report["next_steps"].append("Request compatibility review, or select one of: " + ", ".join(SUPPORTED_VERSIONS) + ".")

        def options():
            result = command_result([str(self.exe), "exec", "--help"], self.directory)
            missing = REQUIRED_OPTIONS - set(re.findall(r"--[a-z][a-z-]*\b", result.stdout))
            if result.returncode:
                raise HarnessError("Cannot inspect codex exec options.")
            if missing:
                raise HarnessError("Missing required options: " + ", ".join(sorted(missing)))

        def features():
            result = command_result([str(self.exe), "features", "list"], self.directory)
            if result.returncode:
                raise HarnessError("Cannot inspect Codex feature controls.")
            for line in result.stdout.splitlines():
                if not line.strip():
                    continue
                fields = line.split()
                if len(fields) < 3 or fields[-1] not in {"true", "false"}:
                    raise HarnessError("Unrecognized feature listing; compatibility review required.")
                if not {"removed", "deprecated"} & set(fields[1:-1]):
                    self.features[fields[0]] = False
            missing = REQUIRED_FEATURES - self.features.keys()
            if missing:
                raise HarnessError("Missing required feature controls: " + ", ".join(sorted(missing)))
            self.features["skip_host_skill_discovery"] = True
            report["features"] = dict(self.features)

        def authentication():
            result = command_result([str(self.exe), "login", "status"], self.directory)
            if result.returncode or "Logged in using ChatGPT" not in result.stdout + result.stderr:
                raise HarnessError("ChatGPT login is unavailable for the selected CLI.")
            report["authentication"] = "chatgpt"

        def model():
            if self.model is None:
                self.model = default_model()
            if not isinstance(self.model, str) or not self.model.strip() or len(self.model) > 100:
                raise HarnessError("A nonempty Codex model name is required.")
            report["model"] = self.model

        check("options", options, "Select a reviewed CLI with the required exec options; do not omit required restrictions.")
        check("features", features, "Select a reviewed CLI with the required tool controls, or request an adapter compatibility review.")
        check("authentication", authentication, "Run the selected executable with 'login' to sign in using ChatGPT, then retry.")
        check("model", model, "Specify --model or configure a model in the Codex user configuration.")
        return report

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

    def diagnose(self):
        from .codex_probe import verify_capabilities
        report = self.inspect()
        if any(check["status"] != "passed" for name, check in report["checks"].items() if name != "probe"):
            return report
        try:
            if hashlib.sha256(self.exe.read_bytes()).hexdigest() != report["binary_hash"]:
                raise HarnessError("Codex executable changed during inspection; retry diagnosis.")
            evidence = verify_capabilities(self)
            if hashlib.sha256(self.exe.read_bytes()).hexdigest() != report["binary_hash"]:
                raise HarnessError("Codex executable changed during the probe; retry diagnosis.")
        except (HarnessError, OSError) as exc:
            report["checks"]["probe"] = {"status": "failed", "detail": str(exc)}
            report["next_steps"].append("Inspect the local probe logs at " + str(self.directory) + "; resolve the failure before planning.")
            return report
        report["checks"]["probe"] = {"status": "passed"}
        report.update(evidence, ready=True, verified_at=time.time(),
                      boundary="text-only; no filesystem, process, app or web tools")
        self.policy = report
        return report

    def verify(self):
        report = self.diagnose()
        if not report["ready"]:
            problems = [name + ": " + check["detail"] for name, check in report["checks"].items()
                        if check["status"] in {"failed", "unverified"}]
            raise HarnessError("Planner is not ready. " + "; ".join(problems) + " " + " ".join(report["next_steps"]))
        return report

    def generate(self, prompt, schema, attempt, launched, timeout=180):
        if self.policy is None:
            raise HarnessError("Verify the Planner capability boundary before a live call.")
        if hashlib.sha256(self.exe.read_bytes()).hexdigest() != self.policy["binary_hash"]:
            raise HarnessError("Codex executable changed after verification.")
        # Planning assigns a unique directory per call; keep filenames short on Windows.
        schema_path = self.directory / "schema.json"
        schema_path.write_text(json.dumps(schema), encoding="utf-8")
        log = self.directory / "events.jsonl"
        errors = self.directory / "stderr.log"
        attempt.update(model=self.model, policy=self.policy, schema=str(schema_path),
                       log=str(log), stderr=str(errors),
                       outcome="launching", started=time.time())
        for key in ("usage", "session_id"):
            attempt.setdefault(key, None)
        attempt.update(dispatch_status="not_sent", actual_ai_call_attempts=0, confirmed_ai_calls=0)

        def observe(phase):
            attempt[phase + "_at"] = time.time()
            callback = getattr(self, "lifecycle", None)
            if callback is not None:
                callback(attempt, phase)

        worker = None
        job = Job()
        try:
            with log.open("wb") as output, errors.open("wb") as error:
                request = json.dumps({"argv": [str(value) for value in self.arguments(schema_path)],
                                      "prompt": prompt}).encode("utf-8")
                worker = subprocess.Popen([sys.executable, "-I", "-B", "-c", LAUNCH_GATE], cwd=self.directory, env=environment(),
                                          stdin=subprocess.PIPE, stdout=output, stderr=error,
                                          creationflags=subprocess.CREATE_NO_WINDOW)
                job.assign(worker.pid)
                attempt.update(process=identity(worker.pid), containment=dict(job.record), outcome="running")
                observe("process_registered")
                launched(attempt)
                # This durable intent precedes input transmission. A crash here cannot
                # establish whether the server received it, so recovery must not retry.
                attempt.update(dispatch_status="uncertain", actual_ai_call_attempts=1, confirmed_ai_calls=None)
                observe("dispatch_intent")
                try:
                    worker.communicate(request, timeout=timeout)
                except subprocess.TimeoutExpired:
                    attempt.update(outcome="interrupted", reason="Planner timeout; inspect recorded dispatch before recovery.")
                    return None
                attempt["exit_code"] = worker.returncode
                if worker.returncode:
                    attempt.update(outcome="unverified", reason="Codex call failed; inspect the recorded logs and login/limits.")
                    return None
        except KeyboardInterrupt:
            attempt.update(outcome="interrupted", reason="Planner interrupted; inspect recorded dispatch before recovery.")
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
            observe_output(log, attempt)
        allowed = (DISABLED_CODE_MODE_NOTICE,) if self.policy.get("profile") == "text-only-v1" else ()
        attempt["notices"] = []
        response, usage = parse_events(log.read_text(encoding="utf-8"), allowed_notices=allowed,
                                       notices=attempt["notices"])
        attempt["usage"] = usage
        attempt.update(outcome="responded", dispatch_status="responded", confirmed_ai_calls=1,
                       response_hash=digest(response))
        observe("responded")
        return response


def observe_output(log, attempt):
    """Preserve facts seen even in a partial/failed stream without verifying a turn."""
    try:
        lines = log.read_text(encoding="utf-8", errors="replace").splitlines()
    except OSError:
        return
    sessions = set()
    for line in lines:
        try:
            event = decode_json(line)
        except HarnessError:
            continue
        if not isinstance(event, dict):
            continue
        if event.get("type") == "thread.started" and isinstance(event.get("thread_id"), str) and event["thread_id"]:
            sessions.add(event["thread_id"])
        if event.get("type") == "turn.completed" and isinstance(event.get("usage"), dict):
            attempt["usage"] = event["usage"]
    if len(sessions) == 1:
        attempt["session_id"] = sessions.pop()


def parse_events(raw, *, allowed_notices=(), notices=None):
    messages, completed, usage = [], False, None
    turn_started = False
    for line in raw.splitlines():
        try:
            event = decode_json(line)
        except HarnessError as exc:
            raise HarnessError("Malformed Codex event stream; response not verified.") from exc
        if not isinstance(event, dict) or not isinstance(event.get("type"), str):
            raise HarnessError("Malformed Codex event; response not verified.")
        if event.get("type") in {"error", "turn.failed"}:
            raise HarnessError("Codex reported an unsuccessful turn; inspect the recorded event log.")
        if event.get("type") == "turn.started":
            turn_started = True
        if event.get("type") == "turn.completed":
            completed, usage = True, event.get("usage")
        item = event.get("item", {})
        if not isinstance(item, dict):
            raise HarnessError("Malformed Codex item; response not verified.")
        if item.get("type") == "error":
            # This exact startup diagnostic describes an intentionally disabled capability.
            # Never ignore it during a turn, or ignore other errors from the CLI/model.
            if (not turn_started and not completed and event["type"] == "item.completed"
                    and item.get("message") in allowed_notices):
                if notices is not None:
                    notices.append(item["message"])
                continue
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
