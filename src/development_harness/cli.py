"""Human commands are the approval boundary of the Phase 1 fake harness."""

import argparse
import json
import os
import sqlite3
import sys

from . import __version__
from .model import HarnessError


def parser():
    result = argparse.ArgumentParser(prog="dev-harness", description="Phase 1 foundation: fake AI, real tests and persistent state.")
    result.add_argument("--version", action="version", version=__version__)
    result.add_argument("--project", default=".", help="Prepared project directory (default: current directory)")
    result.add_argument("--state-dir", help="Local runtime directory outside the project and OneDrive")
    commands = result.add_subparsers(dest="command", required=True)
    prepare = commands.add_parser("prepare", help="Record a JSON fake-Adapter plan and file baseline")
    prepare.add_argument("--plan", required=True)
    commands.add_parser("approve", help="Approve the unchanged recorded plan and starting files")
    for name in ("run", "resume"):
        command = commands.add_parser(name, help="Execute or resume the approved run")
        command.add_argument("--steps", type=int, help="Pause after this many stage boundaries")
    commands.add_parser("status", help="Show state, actual evidence and unexpected file differences")
    commands.add_parser("accept", help="Accept the final verified result")
    commands.add_parser("cancel", help="Cancel the current run; preserve files and all records")
    return result


def main(argv=None):
    args = parser().parse_args(argv)
    if os.name != "nt":
        print("Phase 1 currently supports Windows execution only.", file=sys.stderr)
        return 2
    from .runner import Harness
    try:
        harness = Harness(args.project, args.state_dir)
        if args.command == "prepare":
            harness.prepare(args.plan)
        elif args.command in {"run", "resume"}:
            if args.steps is not None and args.steps < 1:
                raise HarnessError("--steps must be positive.")
            harness.execute(args.steps)
        elif args.command != "status":
            getattr(harness, args.command)()
        result = harness.status()
        print(json.dumps(result, ensure_ascii=True, indent=2))
        if args.command in {"run", "resume"} and (result["reason"] or result["stage"] == "failed"):
            return 1
        return 0
    except (HarnessError, OSError, sqlite3.Error) as exc:
        print(json.dumps({"error": str(exc)}, ensure_ascii=True), file=sys.stderr)
        return 2
