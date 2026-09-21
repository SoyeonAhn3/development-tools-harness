import json
from pathlib import Path
import subprocess

import pytest

from development_harness import codex_adapter as codex
from development_harness.cli import parser
from development_harness.model import HarnessError


@pytest.fixture
def installed_cli(tmp_path, monkeypatch):
    binary = tmp_path / "selected CLI 한글.exe"
    binary.write_bytes(b"synthetic executable; never executed")
    facts = {"version": "codex-cli 0.154.0", "options": set(codex.REQUIRED_OPTIONS),
             "features": set(codex.REQUIRED_FEATURES), "auth": "Logged in using ChatGPT",
             "probe_error": None, "probe_calls": 0, "commands": []}

    def command(argv, directory, timeout=20):
        assert argv[0] == str(binary.resolve())
        args = argv[1:]
        facts["commands"].append(args)
        if args == ["--version"]:
            output = facts["version"]
        elif args == ["exec", "--help"]:
            output = " ".join(sorted(facts["options"]))
        elif args == ["features", "list"]:
            output = facts.get("feature_output", "\n".join(name + " stable true" for name in sorted(facts["features"])))
        elif args == ["login", "status"]:
            output = facts["auth"]
        else:
            raise AssertionError(args)
        return subprocess.CompletedProcess(argv, 0, output, "")

    def probe(adapter):
        facts["probe_calls"] += 1
        assert adapter.features["code_mode_host"] is False
        assert adapter.features["skip_host_skill_discovery"] is True
        if facts["probe_error"]:
            raise HarnessError(facts["probe_error"])
        return {"tool_manifest": [], "rejected_tools": ["apply_patch"], "probe_actual_ai_calls": 0}

    monkeypatch.setattr(codex, "command_result", command)
    monkeypatch.setattr("development_harness.codex_probe.verify_capabilities", probe)
    adapter = codex.CodexPlanner("test-model", tmp_path / "call", codex_path=str(binary))
    return adapter, facts


@pytest.mark.parametrize("version", ["codex-cli 0.154.0", "codex-cli 0.155.1"])
def test_supported_versions_keep_actual_version_and_require_probe(installed_cli, version):
    adapter, facts = installed_cli
    facts["version"] = version
    report = adapter.verify()
    assert report["ready"] is True
    assert report["version"] == version
    assert report["support_status"] == "supported"
    assert report["profile"] == "text-only-v1"
    assert report["supported_versions"] == ["codex-cli 0.154.0", "codex-cli 0.155.1"]
    assert all(check["status"] == "passed" for check in report["checks"].values())
    assert facts["probe_calls"] == 1
    assert report["next_steps"] == []


@pytest.mark.parametrize("version", ["codex-cli 0.153.0", "codex-cli 0.155.0", "codex-cli 0.156.0", "codex-cli 0.155.1-beta.1"])
def test_unreviewed_versions_are_diagnosed_without_probe_or_live_permission(installed_cli, version):
    adapter, facts = installed_cli
    facts["version"] = version
    report = adapter.diagnose()
    assert report["ready"] is False
    assert report["support_status"] == "unverified"
    assert report["checks"]["version"]["status"] == "unverified"
    assert report["checks"]["options"]["status"] == "passed"
    assert report["checks"]["authentication"]["status"] == "passed"
    assert report["checks"]["probe"]["status"] == "not_run"
    assert "compatibility review" in report["next_steps"][0]
    assert facts["probe_calls"] == 0
    assert adapter.policy is None
    with pytest.raises(HarnessError, match="not been reviewed"):
        adapter.verify()
    with pytest.raises(HarnessError, match="Verify the Planner"):
        adapter.generate("must not be sent", {}, {}, lambda _: None)


@pytest.mark.parametrize("kind,missing", [("options", "--ignore-user-config"),
                                          ("options", "--output-schema"),
                                          ("features", "hooks"),
                                          ("features", "skip_host_skill_discovery")])
def test_missing_required_controls_explain_failure_and_block_probe(installed_cli, kind, missing):
    adapter, facts = installed_cli
    facts[kind].remove(missing)
    report = adapter.diagnose()
    assert report["support_status"] == "supported"
    assert report["ready"] is False
    assert report["checks"][kind]["status"] == "failed"
    assert missing in report["checks"][kind]["detail"]
    assert facts["probe_calls"] == 0


def test_option_prefix_does_not_count_as_required_option(installed_cli):
    adapter, facts = installed_cli
    facts["options"].remove("--json")
    facts["options"].add("--json-debug")
    assert adapter.diagnose()["checks"]["options"]["status"] == "failed"


def test_malformed_feature_listing_blocks_execution(installed_cli):
    adapter, facts = installed_cli
    facts["feature_output"] = "hooks stable enabled"
    assert adapter.diagnose()["checks"]["features"]["status"] == "failed"
    assert facts["probe_calls"] == 0


def test_removed_control_is_not_treated_as_available(installed_cli):
    adapter, facts = installed_cli
    facts["feature_output"] = "\n".join(name + (" removed false" if name == "hooks" else " stable true")
                                           for name in facts["features"])
    assert "hooks" in adapter.diagnose()["checks"]["features"]["detail"]


def test_login_failure_is_distinct_from_supported_version(installed_cli):
    adapter, facts = installed_cli
    facts["auth"] = "Not logged in"
    report = adapter.diagnose()
    assert report["support_status"] == "supported"
    assert report["checks"]["authentication"]["status"] == "failed"
    assert "login" in report["next_steps"][0]
    assert facts["probe_calls"] == 0


def test_missing_model_still_reports_version_and_login(installed_cli, monkeypatch):
    adapter, facts = installed_cli
    adapter.model = None
    def no_model():
        raise HarnessError("No model configured")
    monkeypatch.setattr(codex, "default_model", no_model)
    report = adapter.diagnose()
    assert report["version"] == facts["version"]
    assert report["checks"]["authentication"]["status"] == "passed"
    assert report["checks"]["model"]["status"] == "failed"
    assert facts["probe_calls"] == 0


def test_failed_rediagnosis_clears_previous_permission(installed_cli):
    adapter, facts = installed_cli
    adapter.verify()
    facts["probe_error"] = "Unsafe tool manifest: shell"
    report = adapter.diagnose()
    assert report["checks"]["probe"]["status"] == "failed"
    assert "Unsafe tool manifest" in report["checks"]["probe"]["detail"]
    assert report["ready"] is False
    assert adapter.policy is None


def test_binary_change_during_probe_does_not_authorize_execution(installed_cli, monkeypatch):
    adapter, facts = installed_cli
    def replaced(candidate):
        candidate.exe.write_bytes(b"replaced during probe")
        return {}
    monkeypatch.setattr("development_harness.codex_probe.verify_capabilities", replaced)
    report = adapter.diagnose()
    assert report["ready"] is False
    assert "changed during the probe" in report["checks"]["probe"]["detail"]
    assert adapter.policy is None


def test_explicit_path_overrides_environment_and_discovery(tmp_path, monkeypatch):
    explicit = tmp_path / "user selected.exe"
    configured = tmp_path / "machine configured.exe"
    explicit.write_bytes(b"explicit")
    configured.write_bytes(b"environment")
    monkeypatch.setenv(codex.CODEX_PATH_ENV, str(configured))
    monkeypatch.setattr(codex.shutil, "which", lambda _: pytest.fail("Must not fall back to PATH"))
    assert codex.executable(str(explicit)) == explicit.resolve()
    assert codex.executable() == configured.resolve()
    with pytest.raises(HarnessError, match="existing absolute .exe"):
        codex.executable(str(tmp_path / "missing.exe"))


@pytest.mark.parametrize("name", ["relative.exe", "script.cmd", "script.ps1"])
def test_selected_path_must_be_absolute_executable(tmp_path, name):
    path = tmp_path / name
    path.write_bytes(b"not executed")
    selected = name if name == "relative.exe" else str(path)
    with pytest.raises(HarnessError, match="existing absolute .exe"):
        codex.executable(selected)


def test_invalid_environment_path_has_structured_diagnostic(tmp_path, monkeypatch):
    monkeypatch.setenv(codex.CODEX_PATH_ENV, str(tmp_path / "missing.exe"))
    adapter = codex.CodexPlanner("test", tmp_path / "probe")
    report = adapter.diagnose()
    assert report["checks"]["executable"]["status"] == "failed"
    assert report["checks"]["version"]["status"] == "not_run"
    assert report["ready"] is False
    json.dumps(report)


@pytest.mark.parametrize("command", ["doctor", "plan", "plan-resume"])
def test_cli_accepts_explicit_executable(command):
    args = parser().parse_args([command, "--codex-path", "C:\\Tools\\Codex CLI\\codex.exe"])
    assert args.codex_path == "C:\\Tools\\Codex CLI\\codex.exe"


def stream(*events):
    return "\n".join(json.dumps(event) for event in events)


NOTICE = {"type": "item.completed", "item": {"type": "error", "message": codex.DISABLED_CODE_MODE_NOTICE}}
STARTED = {"type": "turn.started"}
RESPONSE = {"type": "item.completed", "item": {"type": "agent_message", "text": '{"ok":true}'}}
COMPLETED = {"type": "turn.completed"}


def test_expected_disabled_capability_notice_is_recorded_before_success():
    notices = []
    response, _ = codex.parse_events(stream(NOTICE, STARTED, RESPONSE, COMPLETED),
                                    allowed_notices=(codex.DISABLED_CODE_MODE_NOTICE,), notices=notices)
    assert response == {"ok": True}
    assert notices == [codex.DISABLED_CODE_MODE_NOTICE]
    with pytest.raises(HarnessError, match="item error"):
        codex.parse_events(stream(NOTICE, STARTED, RESPONSE, COMPLETED))


@pytest.mark.parametrize("events", [(STARTED, NOTICE, RESPONSE, COMPLETED),
                                     (NOTICE, STARTED, {"type": "turn.failed"}),
                                     (NOTICE, STARTED, RESPONSE),
                                     ({"type": "item.completed", "item": {"type": "error", "message": "other error"}},
                                      STARTED, RESPONSE, COMPLETED)])
def test_startup_notice_does_not_hide_real_failures(events):
    with pytest.raises(HarnessError):
        codex.parse_events(stream(*events), allowed_notices=(codex.DISABLED_CODE_MODE_NOTICE,))
