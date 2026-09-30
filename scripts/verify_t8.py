"""Run the installed runner's offline isolation/workflow/resume proofs."""

import argparse
from pathlib import Path
import subprocess
import uuid

from development_harness.frozen_entry import inspect_runner
from development_harness.store import default_home


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--runner", required=True)
    parser.add_argument("--directory", help="Fresh evidence directory outside the runner and repository")
    args = parser.parse_args()
    runner = Path(args.runner).resolve()
    inspect_runner(runner)
    directory = Path(args.directory).resolve() if args.directory else default_home().parent / "t8-verification" / uuid.uuid4().hex[:10]
    result = subprocess.run([str(runner / "runtime/python.exe"), "-I", "-B", "-m", "development_harness.fixed_runner_verify",
                             "--repository", str(Path(__file__).resolve().parents[1]), "--runner", str(runner),
                             "--directory", str(directory)], creationflags=subprocess.CREATE_NO_WINDOW)
    return result.returncode


if __name__ == "__main__":
    raise SystemExit(main())
