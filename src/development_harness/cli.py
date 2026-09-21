"""Human commands for real planning and separate Phase 1 execution fixtures."""

import argparse
import json
import os
import sqlite3
import sys

from . import __version__
from .model import HarnessError


def parser():
    result = argparse.ArgumentParser(prog="dev-harness", description="Local development harness: real planning and explicit fake execution fixtures.")
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
    registration = commands.add_parser("register", help="Register a project specification, source inputs and baseline commands")
    registration.add_argument("--spec", required=True, help="Relative specification path within --project")
    registration.add_argument("--context", nargs="*", default=[], help="Explicit relative related-code file paths")
    registration.add_argument("--validation", required=True, help="JSON file containing the validation command array")
    registration.add_argument("--model", help="Codex model (defaults to the configured user model)")
    registration.add_argument("--planner-timeout", type=int, default=240)
    doctor = commands.add_parser("doctor", help="Check ChatGPT login and prove the installed CLI's Planner capability boundary")
    doctor.add_argument("--model")
    doctor.add_argument("--codex-path", help="Absolute Codex .exe path (overrides DEVELOPMENT_HARNESS_CODEX_PATH)")
    for name, help_text in {
        "baseline": "Run registered baseline checks without an AI call",
        "plan": "Validate the baseline and generate a real bilingual plan",
        "plan-resume": "Resume interrupted planning explicitly",
        "plan-status": "Inspect planning evidence and generated documents",
        "plan-approve": "Approve the reviewed plan version; does not execute implementation",
        "plan-cancel": "Cancel planning while preserving files and evidence",
    }.items():
        command = commands.add_parser(name, help=help_text)
        if name in {"plan", "plan-resume"}:
            command.add_argument("--codex-path", help="Absolute Codex .exe path (overrides DEVELOPMENT_HARNESS_CODEX_PATH)")
    revision = commands.add_parser("plan-revise", help="Import an edited plan JSON as a new review version")
    revision.add_argument("--from", dest="revision_path", required=True)
    return result


def main(argv=None):
    args = parser().parse_args(argv)
    if os.name != "nt":
        print("The harness currently supports Windows execution only.", file=sys.stderr)
        return 2
    from .runner import Harness
    try:
        if args.command in {"register", "doctor", "baseline", "plan", "plan-resume", "plan-status", "plan-approve", "plan-revise", "plan-cancel"}:
            return planning_main(args)
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


def planning_main(args):
    from .codex_adapter import CodexPlanner, default_model
    from .planning import Planning
    from .project import read_json
    import uuid

    planner = Planning(args.project, args.state_dir)
    if args.command == "doctor":
        adapter = CodexPlanner(args.model, planner.store.directory / "doctor" / uuid.uuid4().hex,
                               codex_path=args.codex_path)
        report = adapter.diagnose()
        print(json.dumps(report, ensure_ascii=True, indent=2))
        return 0 if report["ready"] else 1
    if args.command == "register":
        planner.register({"version": 1, "spec": args.spec, "context": args.context,
                          "validation": read_json(args.validation), "model": args.model or default_model(),
                          "planner_timeout": args.planner_timeout})
    elif args.command in {"baseline", "plan", "plan-resume"}:
        planner.plan(baseline_only=args.command == "baseline", codex_path=getattr(args, "codex_path", None))
    elif args.command == "plan-approve":
        planner.approve()
    elif args.command == "plan-revise":
        planner.revise(args.revision_path)
    elif args.command == "plan-cancel":
        planner.cancel()
    result = planner.status()
    print(json.dumps(result, ensure_ascii=True, indent=2))
    return int(args.command in {"baseline", "plan", "plan-resume"} and bool(result.get("reason") or result.get("inspection_error")))
