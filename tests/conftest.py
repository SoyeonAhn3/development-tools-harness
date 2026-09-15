import json
from pathlib import Path

import pytest

from development_harness.runner import Harness


@pytest.fixture
def workspace(tmp_path):
    project = tmp_path / "project with spaces 한글"
    project.mkdir()
    (project / "value.py").write_text("VALUE = 0\n", encoding="utf-8")
    (project / "test_value.py").write_text("from value import VALUE\ndef test_value():\n    assert VALUE == 1\n", encoding="utf-8")
    plan = {
        "phase": "foundation-example",
        "tasks": [{"id": "task-1", "writes": [{"value.py": "VALUE = 1\n"}]}],
        "validation": [{"argv": ["{python}", "-m", "pytest", "-q"], "kind": "pytest", "timeout": 30}],
    }
    plan_path = tmp_path / "plan.json"
    def save():
        plan_path.write_text(json.dumps(plan), encoding="utf-8")
    save()
    harness = Harness(project, tmp_path / "state")
    return harness, plan, plan_path, save


@pytest.fixture
def fast_validation(monkeypatch):
    """Exercise state decisions independently from real-process integration tests."""
    def validate(check, project, directory, attempt, launched):
        attempt.update(outcome="passed", tests=1, ended=attempt["started"] + 0.1, duration=0.1)
        return attempt
    monkeypatch.setattr("development_harness.runner.validate", validate)
