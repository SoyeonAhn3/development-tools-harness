"""Human commands for real planning/workflow and separate Phase 1 fixtures."""

import argparse
import json
import os
import sqlite3
import sys

from . import __version__
from .model import HarnessError


def parser():
    result = argparse.ArgumentParser(prog="dev-harness", description="Local development harness: approved planning, implementation, tests and review.")
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
    worker_doctor = commands.add_parser("workflow-doctor", help="Probe Windows worker permissions on synthetic files; no AI execution")
    worker_doctor.add_argument("--backend", choices=("appcontainer", "codex-unelevated"), default="appcontainer",
                               help="Candidate to investigate (default: administrator-free AppContainer)")
    worker_doctor.add_argument("--codex-path", help="Absolute Codex .exe path (overrides DEVELOPMENT_HARNESS_CODEX_PATH)")
    workflow_prepare = commands.add_parser("workflow-prepare", help="Prepare execution records from the approved current Phase; no AI call")
    workflow_prepare.add_argument("--planning-run", help="Latest approved planning run ID (defaults to latest planning run)")
    workflow_prepare.add_argument("--max-corrections", type=int, help="Additional corrections per Task (default: 2; fixed at preparation)")
    workflow_prepare.add_argument("--manual-checks", help="JSON array of required manual checks to pin before execution approval")
    commands.add_parser("workflow-approve", help="Authorize this exact plan/code/policy for execution; no automatic dispatch")
    commands.add_parser("workflow-status", help="Show execution admission, durable attempts, waits and findings")
    commands.add_parser("workflow-cancel", help="Cancel workflow admission; preserve files and records")
    workflow_run = commands.add_parser("workflow-run", help="Execute approved Tasks sequentially with isolated checks and independent review")
    workflow_run.add_argument("--codex-path", help="Absolute reviewed Codex .exe path")
    workflow_run.add_argument("--steps", type=int, help="Stop after this many completed stage boundaries; use workflow-resume after an interruption")
    workflow_resume = commands.add_parser("workflow-resume", help="Inspect and recover an interrupted workflow, then continue approved work")
    workflow_resume.add_argument("--codex-path", help="Absolute reviewed Codex .exe path")
    workflow_resume.add_argument("--steps", type=int, help="Limit completed recovery/execution boundaries")
    commands.add_parser("workflow-report", help="Show delivered files, evidence, unresolved items and acceptance conditions")
    commands.add_parser("workflow-accept", help="Explicitly accept the current result after all mandatory evidence passes")
    commands.add_parser("workflow-replan", help="Start fresh planning on current files after changed-requirements feedback; no AI call")
    feedback = commands.add_parser("workflow-feedback", help="Record a same-scope defect or changed requirements without dispatch")
    feedback.add_argument("--kind", required=True, choices=("defect", "requirements"))
    feedback.add_argument("--task", help="Approved Task ID for a same-scope defect")
    feedback.add_argument("--feedback-id", help="Optional stable identity for repeat submissions")
    feedback_text = feedback.add_mutually_exclusive_group(required=True)
    feedback_text.add_argument("--text", help="Original feedback text")
    feedback_text.add_argument("--from", dest="text_file", help="UTF-8 file with original feedback text")
    reuse = commands.add_parser("workflow-reuse", help="Record how final registered checks verify a current reused requirement")
    reuse.add_argument("--requirement", required=True)
    reuse.add_argument("--validation-ids", nargs="+", required=True, help="Passing final validation attempt IDs from workflow-report")
    manual = commands.add_parser("workflow-manual", help="Record a result of a manual check pinned before execution approval")
    manual.add_argument("--check", required=True)
    for command in (reuse, manual):
        command.add_argument("--outcome", required=True, choices=("passed", "failed"))
        command.add_argument("--record-id", help="Optional stable confirmation identity")
        note = command.add_mutually_exclusive_group(required=True)
        note.add_argument("--evidence", help="Observed result and explanation")
        note.add_argument("--evidence-file", help="UTF-8 file containing the observed result and explanation")
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
        if args.command == "workflow-doctor":
            from .store import Store
            import uuid
            if args.backend == "appcontainer" and args.codex_path:
                raise HarnessError("--codex-path requires --backend codex-unelevated; AppContainer does not use Codex.")
            store = Store(args.project, args.state_dir)
            directory = store.home / "worker-probes" / uuid.uuid4().hex
            if args.backend == "appcontainer":
                from .appcontainer_probe import diagnose_appcontainer
                report = diagnose_appcontainer(directory)
            else:
                from .worker_probe import diagnose_workers
                report = diagnose_workers(directory, codex_path=args.codex_path)
            print(json.dumps(report, ensure_ascii=True, indent=2))
            return 0 if report["ready"] else 1
        if args.command in {"register", "doctor", "baseline", "plan", "plan-resume", "plan-status", "plan-approve", "plan-revise", "plan-cancel"}:
            return planning_main(args)
        if args.command == "workflow-replan":
            from .planning import Planning
            planner = Planning(args.project, args.state_dir)
            planner.replan()
            print(json.dumps(planner.status(), ensure_ascii=True, indent=2))
            return 0
        if args.command in {"workflow-prepare", "workflow-approve", "workflow-status", "workflow-cancel", "workflow-run", "workflow-resume",
                            "workflow-report", "workflow-accept", "workflow-feedback", "workflow-reuse", "workflow-manual"}:
            from .workflow import Workflow
            workflow = Workflow(args.project, args.state_dir)
            if args.command == "workflow-prepare":
                from .project import read_json
                workflow.prepare(args.planning_run, max_corrections=args.max_corrections,
                                 manual_checks=read_json(args.manual_checks) if args.manual_checks else None)
            elif args.command == "workflow-run":
                workflow.execute(codex_path=args.codex_path, steps=args.steps)
            elif args.command == "workflow-resume":
                workflow.resume(codex_path=args.codex_path, steps=args.steps)
            elif args.command == "workflow-feedback":
                workflow.feedback(read_note(args.text_file) if args.text_file else args.text,
                                  kind=args.kind, task_id=args.task, feedback_id=args.feedback_id)
            elif args.command in {"workflow-reuse", "workflow-manual"}:
                evidence = read_note(args.evidence_file) if args.evidence_file else args.evidence
                if args.command == "workflow-reuse":
                    workflow.record_reuse(args.requirement, args.validation_ids, evidence,
                                          outcome=args.outcome, record_id=args.record_id)
                else:
                    workflow.record_manual(args.check, args.outcome, evidence, record_id=args.record_id)
            elif args.command not in {"workflow-status", "workflow-report"}:
                getattr(workflow, args.command.removeprefix("workflow-"))()
            result = workflow.report() if args.command in {"workflow-report", "workflow-accept", "workflow-feedback", "workflow-reuse", "workflow-manual"} else workflow.status()
            print(json.dumps(result, ensure_ascii=True, indent=2))
            if args.command == "workflow-feedback" and result["stage"] == "replanning_required":
                return 0  # The recorded route deliberately invalidates the old plan.
            return int(bool(result.get("inspection_error")) or
                       result.get("outcome") in {"failure", "interrupted", "permission_failure", "unverified"} or
                       args.command in {"workflow-run", "workflow-resume"} and result["stage"] in {"failed", "stopped", "cancelled"})
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


def read_note(path):
    from pathlib import Path
    source = Path(path)
    if source.stat().st_size > 32_000:
        raise HarnessError("Feedback/evidence file exceeds its size limit.")
    try:
        return source.read_text(encoding="utf-8")
    except UnicodeError as exc:
        raise HarnessError("Feedback/evidence file must contain UTF-8 text.") from exc


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
