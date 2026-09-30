"""Real AppContainer resource/state scoping and incomplete-suite reporting."""

import json
from pathlib import Path
import shutil
import uuid

import pytest

from development_harness import __file__ as package_file
from development_harness.files import snapshot
from development_harness.phase_docs import skill_directory
from development_harness.validation_profiles import RESOURCE_FILES, SELF_TEST_PROFILE
from test_workflow_permissions import validation_environment


CHECK = {"kind": "pytest", "argv": ["{python}", "-m", "pytest", "-q"],
         "timeout": 60, "profile": SELF_TEST_PROFILE}

TESTS = '''import os
from pathlib import Path
from development_harness import phase_docs, store

def test_resources_are_b_data_and_not_extra_agent_files():
    project = Path.cwd()
    assert Path(phase_docs.__file__).is_relative_to(project / 'src')
    assert phase_docs.skill_directory() == project / '.agents/skills/phase-doc'
    assert phase_docs.load_profile()['sha256']
    assert not (project / '.agents/unrelated.txt').exists()
    assert not (project / 'README.md').exists()  # Unhashed prose is not a hidden input.

def test_default_database_stays_in_granted_scratch(tmp_path):
    scratch = Path(os.environ['TEMP'])
    assert store.default_home().is_relative_to(scratch)
    db = store.Store(tmp_path, store.default_home())
    db.save({'id': 'self-test', 'stage': 'new'}, 'test', new=True)
    assert db.path.is_relative_to(scratch)
    assert db.get('self-test')['stage'] == 'new'
'''


@pytest.mark.parametrize("drop_test", [False, True])
def test_actual_self_profile_resources_state_and_coverage(validation_environment, drop_test):
    root, validator = validation_environment
    project = root / ("self-" + uuid.uuid4().hex[:8])
    shutil.copytree(Path(package_file).parent, project / "src/development_harness",
                    ignore=shutil.ignore_patterns("__pycache__", "*.pyc", "_phase_doc"))
    files = {"pyproject.toml": '[project]\nname="development-tools-harness"\n',
             "requirements-dev.lock": "", "tests/conftest.py": "",
             "tests/unit/test_self.py": TESTS,
             "tests/integration/test_host.py": "raise RuntimeError('host test must not execute inside AppContainer')\n",
             ".agents/unrelated.txt": "must remain excluded", "README.md": "not a declared test input"}
    for name in RESOURCE_FILES:
        files[name] = (skill_directory() / name.split("phase-doc/", 1)[1]).read_text(encoding="utf-8")
    if drop_test:
        files["tests/conftest.py"] = "def pytest_collection_modifyitems(items):\n    items.pop()\n"
    for name, content in files.items():
        path = project / name
        path.parent.mkdir(parents=True, exist_ok=True)
        path.write_text(content, encoding="utf-8")
    before = snapshot(project)
    result = validator.run(CHECK, project)
    assert snapshot(project) == before
    assert result["outcome"] == ("unverified" if drop_test else "passed"), result
    profile = result["validation_profile"]
    assert snapshot(Path(result["copied_project"])) == profile["inputs"]
    assert profile["isolated_complete"] is not drop_test
    assert profile["all_tests_complete"] is False and profile["host_verification"] == "pending"
    assert len(profile["host_modules"]) == 1
    observed = json.loads(Path(result["collection"]).read_text())
    assert len(observed["discovered"]) == 2
    assert len(observed["passed"]) == (1 if drop_test else 2)
