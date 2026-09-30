"""Host-only bootstrap for an explicitly reviewed complete B regression."""

from importlib import metadata, util
import json
import os
from pathlib import Path
import sys


def main():
    line = sys.stdin.buffer.readline()  # Parent assigns the kill-on-close job first.
    if not line:
        return 125
    config = json.loads(line)
    if sys.version_info[:2] != (3, 12):
        raise RuntimeError("Reviewed host tests require Python 3.12.")
    versions = {name: metadata.version(name) for name in config["dependencies"]}
    if versions != config["dependencies"]:
        raise RuntimeError("Host test dependencies differ from the reviewed lock.")
    import pytest
    spec = util.spec_from_file_location("_controller_collection", config["observer"])
    observer = util.module_from_spec(spec)
    spec.loader.exec_module(observer)
    project = Path(config["project"])
    os.chdir(project)
    sys.path[:0] = [str(project / "src"), str(project)]
    import development_harness
    origin = Path(development_harness.__file__).resolve()
    if not origin.is_relative_to(project / "src"):
        raise RuntimeError("Host tests must import the reviewed B copy.")
    Path(config["environment"]).write_text(json.dumps({"python": sys.executable,
        "dependencies": versions, "module_origin": str(origin)}), encoding="utf-8")
    return pytest.main(config["args"], plugins=[observer.CollectionEvidence(config["collection"])])


if __name__ == "__main__":
    raise SystemExit(main())
