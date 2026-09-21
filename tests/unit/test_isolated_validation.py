import pytest

from development_harness import isolated_validation as module
from development_harness.model import HarnessError


@pytest.mark.parametrize("argv", [["powershell.exe", "-Command", "anything"],
                                  ["{python}", "-m", "pip", "install", "anything"],
                                  ["other-python.exe", "-m", "pytest"],
                                  ["{python}", "-m", "pytest", "--basetemp", "C:/outside"],
                                  ["{python}", "-m", "pytest", "--capture=fd"],
                                  ["{python}", "-m", "pytest", "--junitxml", "forged.xml"]])
def test_unreviewed_commands_and_evidence_overrides_rejected(argv):
    with pytest.raises(HarnessError):
        module.pytest_arguments({"argv": argv, "kind": "pytest", "timeout": 30})


def test_validator_requires_real_permission_proof(tmp_path):
    project = tmp_path / "project"
    project.mkdir()
    validator = module.IsolatedValidator(tmp_path / "sandbox")
    with pytest.raises(HarnessError, match="Verify the AppContainer"):
        validator.run({"argv": ["{python}", "-m", "pytest"], "kind": "pytest", "timeout": 30}, project)


def test_dependency_mismatch_does_not_copy_or_install_runtime(tmp_path, monkeypatch):
    class WrongVersion:
        version = "unreviewed"
        files = ["not-used"]
    monkeypatch.setattr(module.metadata, "distribution", lambda _: WrongVersion())
    monkeypatch.setattr(module, "copy_runtime", lambda _: pytest.fail("Do not start after a dependency mismatch"))
    with pytest.raises(HarnessError, match="reviewed lock"):
        module.copy_validation_runtime(tmp_path / "runtime")
    assert not list(tmp_path.iterdir())
