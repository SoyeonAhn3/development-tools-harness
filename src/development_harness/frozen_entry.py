"""Standard-library-only entry point copied beside a frozen runner's manifest.

Run with that runner's python.exe -I -B. Hashes detect accidental changes; the
AppContainer boundary, not this manifest, denies writes by generated code.
"""

import hashlib
import json
import os
from pathlib import Path
import sys


MANIFEST = "runner-manifest.json"


def fingerprint(value):
    return hashlib.sha256(json.dumps(value, sort_keys=True, ensure_ascii=True).encode()).hexdigest()


def plain_path(path):
    path = Path(path).absolute()
    for part in (path, *path.parents):
        if part.is_symlink() or part.is_junction():
            raise ValueError("Frozen runner paths cannot contain links: " + str(part))
    return path


def file_hash(path, *, checked_parent=False):
    if not checked_parent:
        plain_path(path)
    elif Path(path).is_symlink() or Path(path).is_junction():
        raise ValueError("Frozen runner paths cannot contain links: " + str(path))
    with Path(path).open("rb") as stream:
        before = os.fstat(stream.fileno())
        if before.st_nlink != 1:
            raise ValueError("Frozen runner files must have one link: " + str(path))
        result = hashlib.file_digest(stream, "sha256").hexdigest()
        after = os.fstat(stream.fileno())
    if (before.st_size, before.st_mtime_ns, before.st_ino) != (after.st_size, after.st_mtime_ns, after.st_ino):
        raise ValueError("Frozen runner changed during inspection: " + str(path))
    return result


def inventory(root):
    root = plain_path(root)
    files = {}
    for directory, folders, names in os.walk(root, followlinks=False):
        base = Path(directory)
        for name in folders:
            path = base / name
            if path.is_symlink() or path.is_junction():
                raise ValueError("Frozen runner paths cannot contain links: " + str(path))
        for name in sorted(names):
            path = base / name
            if path == root / MANIFEST:
                continue
            files[path.relative_to(root).as_posix()] = file_hash(path, checked_parent=True)
    return files


def inspect_runner(root):
    root = plain_path(root).resolve(strict=True)
    file_hash(root / MANIFEST)
    manifest = json.loads((root / MANIFEST).read_text(encoding="utf-8"))
    if not isinstance(manifest, dict) or manifest.get("format") != 1:
        raise ValueError("Unsupported frozen runner manifest.")
    if manifest.get("artifact_id") != fingerprint({k: v for k, v in manifest.items() if k != "artifact_id"}):
        raise ValueError("Frozen runner manifest identity changed.")
    actual, expected = inventory(root), manifest.get("files", {})
    if not isinstance(expected, dict) or not expected or actual != expected:
        changed = sorted(set(actual) | set(expected)) if not isinstance(expected, dict) else [
            name for name in sorted(set(actual) | set(expected)) if actual.get(name) != expected.get(name)]
        raise ValueError("Frozen runner content changed: " + ", ".join(changed[:12]))
    required = {"run.py", "runtime/python.exe", "tools/codex.exe", "policy.json",
                "runtime/Lib/site-packages/development_harness/__init__.py"}
    if not required <= actual.keys():
        raise ValueError("Frozen runner is missing required installed artifacts.")
    return manifest


def current_artifact_id():
    """Bind new workflow approvals to their installed runner, without migration.

    The launcher checks all files before dispatch. This lightweight comparison
    additionally prevents resuming that workflow from another installation.
    """
    module = Path(__file__).resolve()
    if module.parent.name != "development_harness" or module.parents[3].name != "runtime":
        return None  # Ordinary development installations keep their existing contract.
    root = module.parents[4]
    manifest = json.loads((root / MANIFEST).read_text(encoding="utf-8"))
    if manifest.get("artifact_id") != fingerprint({k: v for k, v in manifest.items() if k != "artifact_id"}):
        raise ValueError("Frozen runner manifest identity changed.")
    if Path(sys.executable).resolve() != root / "runtime/python.exe":
        raise ValueError("Frozen modules require their own Python runtime.")
    return manifest["artifact_id"]


def overlap(left, right):
    left, right = Path(left).resolve(), Path(right).resolve()
    return left.is_relative_to(right) or right.is_relative_to(left)


def guard_paths(root, project, state):
    project, state = plain_path(project).resolve(), plain_path(state).resolve()
    if any(overlap(a, b) for a, b in ((root, project), (root, state), (project, state))):
        raise ValueError("Frozen runner, target project and runtime storage must be separate, non-nested directories.")
    if any(part.lower().startswith("onedrive") for path in (Path(root), state) for part in path.parts):
        raise ValueError("Frozen runner and runtime storage must be outside OneDrive.")


def installed_info(root, manifest):
    from importlib import metadata
    from development_harness import __version__, phase_docs
    from development_harness.workers import INSTRUCTIONS, REVIEWER_FOLLOWUP_INSTRUCTIONS

    site = root / "runtime/Lib/site-packages"
    origins = {}
    for name in ("development_harness", "psutil", "pytest"):
        module = __import__(name)
        origin = Path(module.__file__).resolve()
        if not origin.is_relative_to(site):
            raise ValueError("Module escaped the frozen installation: " + name)
        origins[name] = str(origin)
    versions = {name: metadata.version(name) for name in manifest["dependencies"]}
    if versions != manifest["dependencies"] or __version__ != manifest["harness_version"]:
        raise ValueError("Installed versions differ from the frozen manifest.")
    policy = json.loads((root / "policy.json").read_text(encoding="utf-8"))
    if (policy["role_instructions"] != INSTRUCTIONS or
            policy["review_followup_instructions"] != REVIEWER_FOLLOWUP_INSTRUCTIONS or
            policy["writing_profile_hash"] != phase_docs.load_profile()["sha256"]):
        raise ValueError("Installed instructions differ from the frozen policy.")
    if not phase_docs.skill_directory().resolve().is_relative_to(site):
        raise ValueError("Writing instructions escaped the frozen installation.")
    return {"artifact_id": manifest["artifact_id"], "root": str(root), "python": sys.executable,
            "harness_version": __version__, "origins": origins, "dependencies": versions,
            "writing_profile_hash": policy["writing_profile_hash"], "codex": manifest["codex"],
            "integrity_verified": True}


def main():
    try:
        root = Path(__file__).resolve().parent
        if not sys.flags.isolated or not sys.dont_write_bytecode:
            raise ValueError("Launch with the frozen runtime's python.exe -I -B run.py.")
        if Path(sys.executable).resolve() != root / "runtime/python.exe":
            raise ValueError("Use this runner's independent Python runtime.")
        manifest = inspect_runner(root)
        info = installed_info(root, manifest)
        if sys.argv[1:] == ["--runner-info"]:
            print(json.dumps(info, ensure_ascii=True, indent=2))
            return 0
        from development_harness.cli import parser, main as cli_main
        from development_harness.store import default_home

        args = parser().parse_args()
        guard_paths(root, args.project, args.state_dir or default_home())
        pinned_codex = root / "tools/codex.exe"
        selected = getattr(args, "codex_path", None)
        if selected is not None and Path(selected).resolve() != pinned_codex:
            raise ValueError("Frozen runner requires its pinned Codex executable.")
        for name in ("PYTHONPATH", "PYTHONHOME", "PYTHONUSERBASE", "PYTHONSTARTUP"):
            os.environ.pop(name, None)
        os.environ["DEVELOPMENT_HARNESS_CODEX_PATH"] = str(pinned_codex)
        os.environ["PYTHONDONTWRITEBYTECODE"] = "1"
        return cli_main()
    except (OSError, ValueError, KeyError, TypeError) as exc:
        print(json.dumps({"error": str(exc)}, ensure_ascii=True), file=sys.stderr)
        return 2


if __name__ == "__main__":
    raise SystemExit(main())
