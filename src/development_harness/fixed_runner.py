"""Prepare a new offline, non-editable runner; never update an existing runner."""

from datetime import datetime, timezone
from importlib import metadata
import json
from pathlib import Path, PurePosixPath
import shutil
import subprocess
import sys
import tempfile
import zipfile

from .codex_adapter import SUPPORTED_VERSIONS, command_result, executable
from .files import snapshot
from .frozen_entry import MANIFEST, file_hash, fingerprint, inspect_runner, inventory, overlap, plain_path
from .isolated_validation import DISTRIBUTIONS, copy_validation_runtime
from .model import HarnessError
from .phase_docs import load_profile
from .store import default_home
from .workers import INSTRUCTIONS, REVIEWER_FOLLOWUP_INSTRUCTIONS


def extract_wheel(wheel, site):
    """Only our pure-Python wheel; reject startup hooks, links and relocation."""
    with zipfile.ZipFile(wheel) as archive:
        seen = set()
        for member in archive.infolist():
            name, path = member.filename, PurePosixPath(member.filename)
            if (path.is_absolute() or ".." in path.parts or "\\" in name or ":" in name or
                    name.casefold() in seen or name.rstrip("/") != path.as_posix() or
                    any(p.endswith(".data") for p in path.parts) or path.suffix in {".pth", ".pyc"} or
                    (member.external_attr >> 16) & 0o170000 == 0o120000 or
                    not (path.parts[0] == "development_harness" or path.parts[0].endswith(".dist-info"))):
                raise HarnessError("Unexpected frozen wheel member: " + name)
            seen.add(name.casefold())
        archive.extractall(site)


def build_runner(repository, destination, *, codex_path=None):
    repository = plain_path(repository).resolve(strict=True)
    destination = plain_path(destination).resolve()
    if overlap(repository, destination) or any(p.lower().startswith("onedrive") for p in destination.parts):
        raise HarnessError("Create the frozen runner outside the source tree and OneDrive.")
    if destination.exists():
        raise HarnessError("Frozen runner destination already exists; preserve it and choose a new directory.")
    if metadata.version("setuptools") != "84.0.0":
        raise HarnessError("Freeze requires the reviewed setuptools==84.0.0 build dependency.")
    # Refuse to package different sources using an unrelated editable interpreter.
    if Path(__file__).resolve() != repository / "src/development_harness/fixed_runner.py":
        raise HarnessError("Run the builder from the selected development checkout's interpreter.")
    codex = executable(codex_path)
    codex_hash = file_hash(codex)
    observed = command_result([str(codex), "--version"], repository)
    version = observed.stdout.strip()
    if observed.returncode or version not in SUPPORTED_VERSIONS:
        raise HarnessError("Freeze requires a previously reviewed Codex CLI version; observed " + repr(version) +
                           ". Select a reviewed executable with --codex-path.")
    sources = {"package": snapshot(repository / "src/development_harness"),
               "writing_rules": snapshot(repository / ".agents/skills/phase-doc"),
               "pyproject": file_hash(repository / "pyproject.toml"),
               "lock": file_hash(repository / "requirements-dev.lock")}
    destination.mkdir(parents=True, exist_ok=False)
    # Build outputs/logs stay outside A. Failed candidates are retained, never promoted.
    build_home = default_home().parent / "runner-builds"
    build_home.mkdir(parents=True, exist_ok=True)
    build = Path(tempfile.mkdtemp(prefix="t8-", dir=build_home))
    source = build / "source"
    source.mkdir()
    shutil.copy2(repository / "pyproject.toml", source / "pyproject.toml")
    shutil.copytree(repository / "src/development_harness", source / "src/development_harness",
                    ignore=shutil.ignore_patterns("__pycache__", "*.pyc"))
    shutil.copytree(repository / ".agents/skills/phase-doc", source / ".agents/skills/phase-doc")
    argv = [sys.executable, "-I", "-B", "-m", "pip", "wheel", "--no-deps", "--no-index",
            "--no-build-isolation", "--wheel-dir", str(build / "wheels"), str(source)]
    result = subprocess.run(argv, cwd=build, capture_output=True, timeout=120,
                            creationflags=subprocess.CREATE_NO_WINDOW)
    (build / "build.stdout.log").write_bytes(result.stdout)
    (build / "build.stderr.log").write_bytes(result.stderr)
    if result.returncode:
        raise HarnessError("Offline wheel build failed; inspect " + str(build))
    wheels = list((build / "wheels").glob("*.whl"))
    if len(wheels) != 1:
        raise HarnessError("Expected exactly one locally built harness wheel.")
    python = copy_validation_runtime(destination / "runtime")
    extract_wheel(wheels[0], destination / "runtime/Lib/site-packages")
    (destination / "artifacts").mkdir()
    shutil.copy2(wheels[0], destination / "artifacts" / wheels[0].name)
    shutil.copy2(repository / "requirements-dev.lock", destination / "artifacts/requirements-dev.lock")
    shutil.copy2(repository / "src/development_harness/frozen_entry.py", destination / "run.py")
    (destination / "tools").mkdir()
    shutil.copy2(codex, destination / "tools/codex.exe")
    if file_hash(codex) != codex_hash or file_hash(destination / "tools/codex.exe") != codex_hash:
        raise HarnessError("Selected adapter changed during freezing.")
    policy = {"role_instructions": INSTRUCTIONS, "review_followup_instructions": REVIEWER_FOLLOWUP_INSTRUCTIONS,
              "writing_profile_hash": load_profile()["sha256"],
              "approval_policy": "Version-bound planning, separate execution approval and result acceptance",
              "validation_policy": "AppContainer, no capabilities; generated tests use disposable storage",
              "updates": "Manual new runner only; preserve previous runner and active records"}
    (destination / "policy.json").write_text(json.dumps(policy, ensure_ascii=True, indent=2), encoding="utf-8")
    if (snapshot(repository / "src/development_harness") != sources["package"] or
            snapshot(repository / ".agents/skills/phase-doc") != sources["writing_rules"] or
            file_hash(repository / "pyproject.toml") != sources["pyproject"] or
            file_hash(repository / "requirements-dev.lock") != sources["lock"]):
        raise HarnessError("Source changed during freezing; candidate is not ready.")
    manifest = {"format": 1, "created": datetime.now(timezone.utc).isoformat(),
                "harness_version": metadata.version("development-tools-harness"),
                "python_version": sys.version, "dependencies": dict(DISTRIBUTIONS),
                "build_dependency": {"setuptools": metadata.version("setuptools")},
                "source": sources, "build_log_directory": str(build),
                "codex": {"version": version, "sha256": codex_hash}, "files": inventory(destination)}
    manifest["artifact_id"] = fingerprint(manifest)
    (destination / MANIFEST).write_text(json.dumps(manifest, ensure_ascii=True, indent=2), encoding="utf-8")
    inspect_runner(destination)
    check = subprocess.run([str(python), "-I", "-B", str(destination / "run.py"), "--runner-info"],
                           cwd=repository, capture_output=True, timeout=60, creationflags=subprocess.CREATE_NO_WINDOW)
    (build / "installed.stdout.json").write_bytes(check.stdout)
    (build / "installed.stderr.log").write_bytes(check.stderr)
    if check.returncode:
        raise HarnessError("Installed origin/policy check failed; inspect " + str(build))
    inspect_runner(destination)
    return json.loads(check.stdout)
