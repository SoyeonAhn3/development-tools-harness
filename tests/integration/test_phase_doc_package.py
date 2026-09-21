"""A non-editable installation must carry the exact project writing resources."""

import json
from pathlib import Path
import shutil
import subprocess
import sys
import zipfile

from development_harness.phase_docs import load_profile


def test_wheel_includes_skill_without_checkout_or_global_skill_dependency(tmp_path):
    repository = Path(__file__).resolve().parents[2]
    build = tmp_path / "source"
    build.mkdir()
    shutil.copyfile(repository / "pyproject.toml", build / "pyproject.toml")
    shutil.copytree(repository / "src/development_harness", build / "src/development_harness",
                    ignore=shutil.ignore_patterns("__pycache__"))
    shutil.copytree(repository / ".agents/skills/phase-doc", build / ".agents/skills/phase-doc")
    wheels = tmp_path / "wheels"
    result = subprocess.run([sys.executable, "-m", "pip", "wheel", "--no-deps", "--no-index",
                             "--no-build-isolation", "--wheel-dir", str(wheels), str(build)],
                            capture_output=True, timeout=90, creationflags=subprocess.CREATE_NO_WINDOW)
    assert result.returncode == 0, result.stdout.decode(errors="replace") + result.stderr.decode(errors="replace")
    installed = tmp_path / "src"  # An installation path may share a source-layout name.
    with zipfile.ZipFile(next(wheels.glob("*.whl"))) as wheel:
        wheel.extractall(installed)
    # A fresh isolated interpreter must resolve resources beside the wheel's module.
    script = """
import json, pathlib, sys
sys.path.insert(0, sys.argv[1])
from development_harness import phase_docs
assert pathlib.Path(phase_docs.__file__).resolve().is_relative_to(pathlib.Path(sys.argv[1]).resolve())
print(json.dumps(phase_docs.load_profile()))
"""
    loaded = subprocess.run([sys.executable, "-I", "-B", "-c", script, str(installed)],
                            cwd=tmp_path, capture_output=True, timeout=15,
                            creationflags=subprocess.CREATE_NO_WINDOW)
    assert loaded.returncode == 0, loaded.stderr.decode(errors="replace")
    assert json.loads(loaded.stdout) == load_profile()
